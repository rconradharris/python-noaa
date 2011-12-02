===========
python-noaa
===========


Description
===========

Python bindings for NOAA's XML web-service as well as a simple command-line
utility for fetching the forecast.


Command-Line Usage
==================

By Zip Code
-----------

::

    $ noaa 78703
    Forecast for 78703
    Fri Chance Rain Showers               57 F    70 F +++++++++++++++++++++++++++++++++++
    Sat Rain Showers Likely               60 F    72 F ++++++++++++++++++++++++++++++++++++
    Sun Rain Showers Likely               53 F    54 F +++++++++++++++++++++++++++
    Mon Chance Rain                       40 F    45 F ++++++++++++++++++++++
    Tue Mostly Sunny                      34 F    47 F +++++++++++++++++++++++

By Location
-----------

::

    $ noaa Austin, TX
    Forecast for Austin, TX, USA
    Fri Chance Rain Showers               57 F    70 F +++++++++++++++++++++++++++++++++++
    Sat Rain Showers Likely               60 F    72 F ++++++++++++++++++++++++++++++++++++
    Sun Rain Showers Likely               53 F    54 F +++++++++++++++++++++++++++
    Mon Chance Rain                       40 F    45 F ++++++++++++++++++++++
    Tue Mostly Sunny                      34 F    47 F +++++++++++++++++++++++

By Coordinates
--------------

::

    $ noaa --metric 30.29128 -97.7385
    Forecast for 30.29128, -97.7385
    Fri Chance Rain Showers               14 C    21 C +++++++++++++++++++++
    Sat Rain Showers Likely               16 C    22 C ++++++++++++++++++++++
    Sun Rain Showers Likely               12 C    12 C ++++++++++++
    Mon Chance Rain                        4 C     7 C +++++++
    Tue Cold                               1 C     8 C ++++++++
