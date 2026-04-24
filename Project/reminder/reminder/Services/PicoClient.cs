using System;
using System.Collections.Generic;
using System.Text;
using System.Text.Json;
using System.Net.Sockets;
using reminder.Models;

namespace reminder.Services
{
    public class PicoClient
    {
        private readonly string _host;
        private readonly int _port;
        public PicoClient(string host, int port)
        {
            _host = host;
            _port = port;
        }
        private async Task<string> SendMessageAsync(object payload)
        {
            using var client = new TcpClient();
            await client.ConnectAsync(_host, _port);

            using var stream = client.GetStream();
            var json = JsonSerializer.Serialize(payload);
            var data = Encoding.UTF8.GetBytes(json);
            
            await stream.WriteAsync(data, 0, data.Length);

            return await ReceiveResponseAsync(stream);
        }

        private async Task<string> ReceiveResponseAsync(NetworkStream stream)
        {
            var buffer = new byte[4096];
            var bytesRead = await stream.ReadAsync(buffer, 0, buffer.Length);
            return Encoding.UTF8.GetString(buffer, 0, bytesRead);
        }

        public async Task<List<EventModel>> GetEventsAsync()
        {
            var resp = await SendMessageAsync(new { cmd = "list" });
            var picoEvents = JsonSerializer.Deserialize<List<PicoEventDto>>(resp) ?? [];

            return picoEvents.Select(e => new EventModel
            {
                Name = e.title,
                Date = DateTime.Parse(e.date)
            }).ToList();
        }

        public async Task AddEventAsync(EventModel ev)
        {
            await SendMessageAsync(new
            {
                cmd = "add",
                title = ev.Name,
                date = ev.Date.ToString("yyyy-MM-dd")
            });
        }

        public async Task DeleteEventAsync(int index)
        {
            await SendMessageAsync(new { cmd = "delete", index });
        }

        //* DTO for deserializing Pico's event format */
        private class PicoEventDto
        {
            public string title { get; set; } = "";
            public string date { get; set; } = "";
        }
    }
}
