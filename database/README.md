### This folder contains the scripts I used to instanciate the demo database.

1) [Download the DS](https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations/data)
2) *Optionaly* sample the data using the `sample_transaction.ipynb` script
3) Run the docker-compose if you dont have a database already
4) run the migration file `00_init.sql` and `01_comment_tables.sql` using `run_migration.py`
5) run the `populate_db.py` script

