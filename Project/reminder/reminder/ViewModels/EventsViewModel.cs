using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using reminder.Models;
using reminder.Services;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Text;
using System.Text.Json;
using reminder.Helpers;


namespace reminder.ViewModels
{
    public partial class EventsViewModel : ObservableObject
    {
        private readonly PicoClient _picoClient;
        private readonly EventStorageService _storageService;

        public ObservableCollection<EventModel> Events { get; } = new();

        [ObservableProperty]
        private EventModel? selectedEvent;

        public EventsViewModel(PicoClient picoClient, EventStorageService storageService)
        {
            _picoClient = picoClient;
            _storageService = storageService;
        }

        [RelayCommand]
        private async Task LoadEventsAsync()
        {
            var events = await _picoClient.GetEventsAsync();
            Events.Clear();
            foreach (var ev in events)
            {
                Events.Add(ev);
            }
        }

        [RelayCommand]
        private async Task AddEventAsync()
        {
            var ev = new EventModel
            {
                Name = "New Event",
                Date = DateTime.Today
            };

            await _picoClient.AddEventAsync(ev);
            await LoadEventsAsync();
        }

        [RelayCommand]
        private async Task Delete()
        {
            if (SelectedEvent is null)
                return;

            var index = Events.IndexOf(SelectedEvent);
            if (index < 0)
                return;

            await _picoClient.DeleteEventAsync(index);
            await LoadEventsAsync();
        }

        [RelayCommand]
        private async Task Import()
        {
            try
            {
                var result = await FilePicker.Default.PickAsync(new PickOptions
                {
                    PickerTitle = "Select events JSON file",
                    FileTypes = CustomFileTypes.Json
                });

                if (result is null)
                    return; // user cancelled

                // Read the file
                var json = await File.ReadAllTextAsync(result.FullPath);

                // Deserialize
                var list = JsonSerializer.Deserialize<List<EventModel>>(json);

                if (list is null)
                    return;

                // Send to Pico
                foreach (var ev in list)
                    await _picoClient.AddEventAsync(ev);

                await LoadEventsAsync();
            }
            catch (Exception ex)
            {
                // TODO: show alert or log
                Console.WriteLine($"Import failed: {ex.Message}");
            }
        }


        [RelayCommand]
        private async Task SaveEventsAsync()
        {
            var path = Path.Combine(FileSystem.AppDataDirectory, "events.json");
            await _storageService.SaveAsync(path, Events);

            await ShareFileAsync(path);
        }

        private async Task ShareFileAsync(string path)
        {
            var file = new FileInfo(path);
            if (file.Exists)
            {
                await Share.RequestAsync(new ShareFileRequest
                {
                    Title = "Share Events",
                    File = new ShareFile(path)
                });
            }
        }
    
    }
}
