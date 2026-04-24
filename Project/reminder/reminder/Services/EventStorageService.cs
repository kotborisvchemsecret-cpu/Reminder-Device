using reminder.Models;
using System;
using System.Collections.Generic;
using System.Text;
using System.Text.Json;

namespace reminder.Services
{
    public class EventStorageService
    {
        public async Task SaveAsync(string path, IEnumerable<EventModel> events)
        {
            var options = new JsonSerializerOptions { WriteIndented = true };
            await File.WriteAllTextAsync(path, JsonSerializer.Serialize(events, options));
        }

        public async Task<List<EventModel>> LoadAsync(string path)
        {
            var json = await File.ReadAllTextAsync(path);
            return JsonSerializer.Deserialize<List<EventModel>>(json) ?? new();
        }
    }
}
