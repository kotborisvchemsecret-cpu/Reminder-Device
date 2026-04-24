using System;
using System.Collections.Generic;
using System.Text;

namespace reminder.Helpers
{
    public class CustomFileTypes
    {
        public static readonly FilePickerFileType Json = new(
        new Dictionary<DevicePlatform, IEnumerable<string>>
        {
            { DevicePlatform.iOS, new[] { "public.json" } },
            { DevicePlatform.MacCatalyst, new[] { "public.json" } },
            { DevicePlatform.Android, new[] { "application/json", "text/json" } },
            { DevicePlatform.WinUI, new[] { ".json" } }
        });
    }
}
