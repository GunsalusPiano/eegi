# Installing `eegi` Project

1. [Development](#development)
1. [Production](#production)


## Development


#### Code

```
git clone https://github.com/katur/eegi.git
cd eegi/eegi
# add localsettings.py; set DEBUG=True
```


#### Database

Add dev database connection info to `eegi/localsettings.py`.
This might be a dev database that already exists on another machine,
or a new database on your own machine.
You might import an existing dump, or you might generate an empty database
from scratch with `./manage.py migrate`. Do whatever suits your needs.


#### Python Dependencies

Python version is listed in [runtime.txt](runtime.txt).

Python package dependencies, including Django,
are listed in [requirements.txt](requirements.txt).
These should be [pip](https://pypi.python.org/pypi/pip)-install into a fresh
[Python virtual environment](http://virtualenv.readthedocs.org/). I use
[virtualenvwrapper](http://virtualenvwrapper.readthedocs.org/en/latest/)
to make working with Python virtual environments easier.

In a nutshell (assuming pip, virtualenv, and virtualenvwrapper installed):
```
mkvirtualenv eegi
workon eegi
pip install -r requirements.txt

# To deactivate virtual environment
deactivate
```


#### CSS/JavaScript Dependencies

To compile SASS to CSS:
```
sass --compile --style compressed website/static/stylesheets/styles.sass
```

Instead of compiling SASS directly,
feel free to use the [Gulp.js build script](gulpfile.js), which watches
for changes in SASS files and automatically compiles.

To set up, assuming [Gulp.js](http://gulpjs.com/) is installed on the system,
run the following in the project root (which will install dependencies
in a git-ignored directory called `node_modules`):
```
npm install --dev-save
```

And to start the gulp build script, run the following in the project root:
```
gulp
```

#### Other Dependencies

A blast feature of the requires a local [blastn](https://blast.ncbi.nlm.nih.gov/Blast.cgi?PAGE_TYPE=BlastDocs&DOC_TYPE=Download)
and [tabix](http://www.htslib.org/) executable that have been added to the path.

This also requires a C. elegans database to be built from a fasta file, and its
corresponding gff annotation file. The sequence names of the fasta file also need
to match those of the annotation file, so 'CHROMOSOME_' has been appended to the
fasta file sequence names.
 ```
wget ftp://ftp.wormbase.org/pub/wormbase/species/c_elegans/sequence/genomic/c_elegans.PRJNA13758.WS260.genomic.fa.gz

wget ftp://ftp.wormbase.org/pub/wormbase/species/c_elegans/sequence/genomic/c_elegans.PRJNA13758.WS260.genomic.fa.gz

gunzip c_elegans.PRJNA13758.WS260.genomic.fa.gz

perl -i.orig -pe 's/^>([A-Za-z]+)/>$1/g' c_elegans.PRJNA13758.WS260.genomic.fa

makeblastdb -in c_elegans.PRJNA13758.WS260.genomic.fa -dbtype nucl

# This was for macOS
sort -V -k1,1 -k4,4 -k5,5 c_elegans.PRJNA13758.WS260.annotations.gff2 > c_elegans.PRJNA13758.WS260.annotations.sorted.gff2

bgzip c_elegans.PRJNA13758.WS260.annotations.sorted.gff2

tabix c_elegans.PRJNA13758.WS260.annotations.sorted.gff2.gz
 ```


#### Running Django's Built-In Development Server

```
./manage.py runserver <IP address>:8000
```


#### Some Other Notes About Development

- There is no need to collect static files in development.
(When DEBUG=True, Django finds static files dynamically across the apps.)



## Production

Here is a walkthrough of how I deployed this with Apache and modwsgi on Ubuntu.

This assumes that most sysadmin setup is already complete.
This sysadmin steps includes the following:

- installing Python and virtualenv
- installing libmysqlclient-dev and libffi-dev
- installing Apache and modwsgi
- installing git
- installing blastn (blast suite)
- installing tabix (samtools)
- installing MySQL
- creating a UNIX user for this project (named eegi)
- creating the project directory at /opt/local/eegi, owned by eegi
- creating a directory for data and backups at /volume/data1/project/eegi, owned by eegi
- creating a MySQL database (eegi)
- creating a MySQL read-write user (eegi) and a MySQL read-only user (eegi_ro)


#### Database

```
mysql -u eegi -p eegi < <sql dump filename>
```


#### Database Backups

```
mkdir /volume/data1/project/eegi/database_backups

mkdir /opt/local/eegi/secret
chmod 700 /opt/local/eegi/secret

touch /opt/local/eegi/secret/eegi.my.cnf
chmod 600 /opt/local/eegi/secret/eegi.my.cnf
vi /opt/local/eegi/secret/eegi.my.cnf
> [client]
> user = eegi_ro
> password = <password>

mkdir /opt/local/eegi/bin
chmod 775 /opt/local/eegi/bin

vi ~/.zshenv
> path=(/opt/local/eegi/bin $path)
source ~/.zshenv

touch /opt/local/eegi/bin/mysqldump_eegi
chmod 774 /opt/local/eegi/bin/mysqldump_eegi
vi /opt/local/eegi/bin/mysqldump_eegi
> #!/bin/sh
>
> /usr/bin/mysqldump --defaults-file=/opt/local/eegi/secret/eegi.my.cnf --single-transaction eegi | pbzip2 -c -p16 > /volume/data1/project/eegi/database_backups/eegi_`date +%Y-%m-%d_%H-%M-%S`.sql.bz2

crontab -e
> 0 4 * * 7 /opt/local/eegi/bin/mysqldump_eegi
```


#### Code

```
cd /opt/local/eegi
git clone https://github.com/katur/eegi.git

cd /opt/local/eegi/eegi/eegi
# add localsettings.py; make sure to set DEBUG=False
```


#### Dependencies

```
cd /opt/local/eegi
virtualenv --python=/usr/bin/python2.7 eegivirtualenv
# NOTE: This use of virtualenv hardcodes the name and location of the virtualenv dir.
# But the --relocatable arg has problems and is to be deprecated.
# So, to move or rename it, delete and recreate the virtualenv dir.

source /opt/local/eegi/eegivirtualenv/bin/activate
pip install -r /opt/local/eegi/eegi/requirements.txt

# for Ubuntu 16 I had to install the following:
apt-get install libmysqlclient-dev and libffi-dev

# install and index analysis software and databases

cd /opt/local/eegi/eegi/analysis_files

wget ftp://ftp.wormbase.org/pub/wormbase/species/c_elegans/sequence/genomic/c_elegans.PRJNA13758.WS260.genomic.fa.gz

wget ftp://ftp.wormbase.org/pub/wormbase/species/c_elegans/gff/c_elegans.PRJNA13758.WS260.annotations.gff2.gz

gunzip c_elegans.PRJNA13758.WS260.genomic.fa.gz

gunzip c_elegans.PRJNA13758.WS260.annotations.gff2.gz

perl -i.orig -pe 's/^>([A-Za-z]+)/>$1/g' c_elegans.PRJNA13758.WS260.genomic.fa

perl -i.orig -pe 's/\'//g' c_elegans.PRJNA13758.WS260.annotations.gff2

makeblastdb -in c_elegans.PRJNA13758.WS260.genomic.fa -dbtype nucl

# This was for macOS
sort -V -k1,1 -k4,4 -k5,5 c_elegans.PRJNA13758.WS260.annotations.gff2 > c_elegans.PRJNA13758.WS260.annotations.sorted.gff2

bgzip c_elegans.PRJNA13758.WS260.annotations.sorted.gff2

tabix c_elegans.PRJNA13758.WS260.annotations.sorted.gff2.gz
```

#### Static Files

```
source /opt/local/eegi/eegivirtualenv/bin/activate
cd /opt/local/eegi/eegi
./manage.py collectstatic
```


#### Apache Configuration

```
mkdir /opt/local/eegi/apache2

vi /opt/local/eegi/apache2/eegi.conf
# Add project-specific apache settings.
# Note that part of this configuration involves serving static files directly.
# Please see the above file, on pyxis, for details.

sudo ln -s /opt/local/eegi/apache2/eegi.conf /etc/apache2/sites-enabled/001-eegi.conf

sudo vi /etc/apache2/ports.conf
# Enable/add line to Listen 80
```


#### Apache Commands
```
sudo service apache2 restart
sudo service apache2 start
sudo service apache2 stop
```


#### Deploying Changes

#### *As project user...*
```
# Dump database and record the currently-deployed git commit,
# in case reverting is necessary

# Activate Python virtual environment
source /opt/local/eegi/eegivirtualenv/bin/activate

# Pull changes
cd /opt/local/eegi/eegi
git pull

# If changes to requirements.txt
pip install -r requirements.txt

# If new/changed static files
./manage.py collectstatic

# If new database migrations
./manage.py migrate

# If any scripts must be run
./manage.py scriptname

# If there are unit tests
./manage.py test
```

#### *As user with sudo...*
```
sudo service apache2 restart
```

If front-end changes, inspect visually.
