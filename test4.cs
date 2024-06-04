using gps_jamming_classifier_be.Data;
using gps_jamming_classifier_be.Models;
using Newtonsoft.Json;
using System.Diagnostics;

namespace gps_jamming_classifier_be.Services
{
    public class SignalProcessingService
    {
        private readonly IServiceScopeFactory _scopeFactory;

        public SignalProcessingService(IServiceScopeFactory scopeFactory)
        {
            _scopeFactory = scopeFactory;
        }

        public async Task<string> ProcessFile(IFormFile file, int numImages, double fs, double time)
        {
            const int chunkSize = 5 * 1024 * 1024; // 5 MB
            long fileLength = file.Length;
            int totalChunks = (int)Math.Ceiling((double)fileLength / chunkSize);
            string filePath = "fileProcess/uploaded_file.bin";

            // Ensure the directory exists
            if (!Directory.Exists("fileProcess"))
            {
                Directory.CreateDirectory("fileProcess");
            }

            using (var fsFile = new FileStream(filePath, FileMode.Create, FileAccess.Write, FileShare.None))
            {
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

                    using (var scope = _scopeFactory.CreateScope())
                    {
                        var context = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();

                        byte[] fileBytes = await File.ReadAllBytesAsync(filePath);

                        var signalData = new SignalData
                        {
                            Data = fileBytes,
                            Description = "Processed signal data",
                            Timestamp = DateTime.UtcNow,
                            Spectrograms = new List<Spectrogram>()
                        };

                        context.SignalDatas.Add(signalData);
                        await context.SaveChangesAsync();
                    }

                    return "File processed and saved to database";
                }
            }
        }
    }
}
