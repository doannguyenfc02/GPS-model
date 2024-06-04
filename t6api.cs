using gps_jamming_classifier_be.Services;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;

namespace gps_jamming_classifier_be.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class FileUploadController : ControllerBase
    {
        private readonly SignalProcessingService _signalProcessingService;

        public FileUploadController(SignalProcessingService signalProcessingService)
        {
            _signalProcessingService = signalProcessingService;
        }

        [HttpPost]
        public async Task<IActionResult> UploadFile(IFormFile file, [FromForm] int numImages, [FromForm] double fs, [FromForm] double time)
        {
            if (file == null || file.Length == 0)
            {
                return BadRequest("No file uploaded.");
            }

            var resultDescription = await _signalProcessingService.ProcessFile(file, numImages, fs, time);
            return Ok(resultDescription);
        }
    }
}
