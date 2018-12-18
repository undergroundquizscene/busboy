First, create an ssh tunnel to the remote machine (which has the database):

```fish
ssh -L 63333:localhost:5432 noel@undergroundquizscene.com
```

Then (in another terminal) use `pg_dump` to copy the data into the database on this machine:

```
pg_dump -h localhost -p 63333 -U noel busboy | psql busboy
```

You can then use the postgresql `copy` command to output the data to a file:

```sql
copy (select * from passage_responses where last_modified > '2018-12-05') to '/Users/Noel/output.csv' with csv delimiter ',' header;
```

It should be possible to use the copy command in the initial dump, to avoid transferring data you don’t need, but I don’t know how to do that yet.
