using Microsoft.Extensions.Logging;
using reminder.Services;
using reminder.ViewModels;

namespace reminder
{
    public static class MauiProgram
    {
        public static MauiApp CreateMauiApp()
        {
            var builder = MauiApp.CreateBuilder();
            builder
                .UseMauiApp<App>()
                .ConfigureFonts(fonts =>
                {
                    fonts.AddFont("OpenSans-Regular.ttf", "OpenSansRegular");
                    fonts.AddFont("OpenSans-Semibold.ttf", "OpenSansSemibold");
                });
            builder.Services.AddSingleton(provider =>
            {
                var ip = Preferences.Get("PicoIp", "");
                return new PicoClient(ip);
            });

            builder.Services.AddSingleton<EventStorageService>();

            builder.Services.AddSingleton<EventsViewModel>();
            builder.Services.AddSingleton<MainPage>();

#if DEBUG
            builder.Logging.AddDebug();
#endif

            return builder.Build();
        }
    }
}
