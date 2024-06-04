using gps_jamming_classifier_be.Data;
using gps_jamming_classifier_be.Models;
using Newtonsoft.Json;
using System.Diagnostics;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.DependencyInjection;
using System.Threading;

namespace gps_jamming_classifier_be.Services
{
    public class SignalProcessingService
    {
        private static readonly SemaphoreSlim _semaphore = new SemaphoreSlim(1, 1);
        private readonly IServiceScopeFactory _scopeFactory;

        public SignalProcessingService(IServiceScopeFactory scopeFactory)
        {
            _scopeFactory = scopeFactory;
        }

        public async Task<string> ProcessFile(IFormFile file, int numImages, double fs, double time)
        {
            await _semaphore.WaitAsync();

            try
            {
                const int chunkSize = 5 * 1024 * 1024; // 5 MB
                long fileLength = file.Length;
                int totalChunks = (int)Math.Ceiling((double)fileLength / chunkSize);

                using (var client = new HttpClient())
                {
                    for (int i = 0; i < totalChunks; i++)
                    {
                        int currentChunkSize = chunkSize;

                        // Adjust the chunk size for the last chunk if it's smaller than chunkSize
                        if (i * chunkSize + chunkSize > fileLength)
                        {
                            currentChunkSize = (int)(fileLength - i * chunkSize);
                        }

                        byte[] buffer = new byte[currentChunkSize];
                        using (var stream = file.OpenReadStream())
                        {
                            stream.Seek(i * (long)chunkSize, SeekOrigin.Begin); // Ensure Seek uses long
                            int bytesRead = await stream.ReadAsync(buffer, 0, currentChunkSize);

                            if (bytesRead < buffer.Length)
                            {
                                Array.Resize(ref buffer, bytesRead);
                            }

                            string base64Chunk = Convert.ToBase64String(buffer);

                            var payload = new
                            {
                                fileData = base64Chunk,
                                chunkIndex = i,
                                totalChunks = totalChunks,
                                numImages = numImages,
                                fs = fs,
                                time = time
                            };

                            var response = await client.PostAsJsonAsync("http://127.0.0.1:5000/upload", payload);
                            response.EnsureSuccessStatusCode();
                        }
                    }

                    var processPayload = new
                    {
                        numImages = numImages,
                        fs = fs,
                        time = time
                    };

                    var finalResponse = await client.PostAsJsonAsync("http://127.0.0.1:5000/upload/completed", processPayload);
                    finalResponse.EnsureSuccessStatusCode();

                    var responseData = JsonConvert.DeserializeObject<dynamic>(await finalResponse.Content.ReadAsStringAsync());

                    // Trigger the prediction process
                    var predictionPayload = new { };
                    var predictionResponse = await client.PostAsJsonAsync("http://127.0.0.1:5000/predict", predictionPayload);
                    predictionResponse.EnsureSuccessStatusCode();

                    var predictions = JsonConvert.DeserializeObject<List<PredictionResult>>(await predictionResponse.Content.ReadAsStringAsync());

                    using (var scope = _scopeFactory.CreateScope())
                    {
                        var context = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();

                        var signalData = new SignalData
                        {
                            Description = "Processed signal data",
                            Timestamp = DateTime.UtcNow,
                            Spectrograms = new List<Spectrogram>()
                        };

                        foreach (var prediction in predictions)
                        {
                            signalData.Spectrograms.Add(new Spectrogram
                            {
                                Data = Convert.FromBase64String(prediction.Base64Image),
                                Description = prediction.Class
                            });
                        }

                        context.SignalDatas.Add(signalData);
                        await context.SaveChangesAsync();
                    }

                    return "File processed and saved to database";
                }
            }
            finally
            {
                _semaphore.Release();
            }
        }
    }

    public class PredictionResult
    {
        public string Image { get; set; } = string.Empty;
        public string Class { get; set; } = string.Empty;
        public string Base64Image { get; set; } = string.Empty;
    }
}
