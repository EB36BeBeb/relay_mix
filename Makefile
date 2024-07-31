build:
    pip install -r requirements.txt -t .

deploy: build
    sam deploy --guided