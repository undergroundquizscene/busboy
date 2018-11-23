First, create an ssh tunnel to the remote machine (which has the database):

```fish
ssh -L 63333:localhost:5432 noel@undergroundquizscene.com
```

Then (in another terminal) use `pg_dump` to copy the data into the database on this machine:

```
pg_dump -h localhost -p 63333 -U noel busboy | psql busboy
```
