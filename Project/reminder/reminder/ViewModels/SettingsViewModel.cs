using System;
using System.Collections.Generic;
using System.Text;

using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;

public partial class SettingsViewModel : ObservableObject
{
    [ObservableProperty]
    private string picoIp = Preferences.Get("PicoIp", "");

    [RelayCommand]
    private void Save()
    {
        Preferences.Set("PicoIp", PicoIp);
    }
}
