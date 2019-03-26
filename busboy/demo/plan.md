```
calculate averages from dataset
every 20 seconds:
  get bus locations
  for any that have arrived:
    remove them from list and log arrival time
  for any others that have changed:
    find what section they’re in
    lookup average travel time from there to here
    update ETA
```
