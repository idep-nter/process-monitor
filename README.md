The main script runs as a daemon and uses ps aux and iotop commands to list top processes for each metric - CPU, MEM and I/O usage - every x seconds (configurable in the yml file) and saves them into the output file with time and date for each log.

The report script on the other hand will output statistics in the given time frame such as average, max, median and percentile of each metric for each process and also top n processes (again configurable) with the highest values during the specified time period.
