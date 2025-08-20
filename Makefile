kr_venv:
	python3 -m venv kr_venv
	kr_venv/bin/pip install poetry
	kr_venv/bin/poetry sync

geoname.db:
	curl -L -o allCountries.zip https://download.geonames.org/export/dump/allCountries.zip
	unzip allCountries.zip allCountries.txt
	sqlite3 geoname.db < geoname.sql
	rm allCountries.zip allCountries.txt

