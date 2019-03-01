#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "eegi.settings")
    
    import ptvsd
    from eegi import settings
    if settings.DEBUG:
        import ptvsd       

        ptvsd.enable_attach(address=("0.0.0.0", 3000))

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
