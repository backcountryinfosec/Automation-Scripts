# Automation-Scripts
Random scripts to automate various things.


## censys_monitor.py
Used to monitor censys.io API for newly created SSL certs that match a specific pattern. Using it as an early detection for new phishing domains. Quite successful so far :).
Example usage in cron:
    0 */3 * * * /opt/censys/venv/bin/python /opt/censys/censys_monitor.py
    
## viper_monitor.py
Monitors directory and uploads any file that's placed there to the [Viper Framework](https://github.com/viper-framework/viper). Also checks Virus Total for matches with an API key.

## dynamic_cloudflare.py
Updates cloudflare with your IP. Helpful if you don't have anything else to update it and are on a dynamic IP from your ISP. 
Example usage in cron:
    */5 * * * * /opt/Cloudflare_Scripts/dynamicDNS.py dyn.domain.tech
