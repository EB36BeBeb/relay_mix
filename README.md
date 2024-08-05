#Relay Mix Repo


## 다음과 같은 권한을 가진 AWS CLI 설정


## API Server Test
```
python -m venv .relay_mix_venv
source .relay_mix_venv
pip install -r requirements.txt
pytest
```
aws 셋팅 전까지는 pytest는 실패해요

## Manual Deploy
serverless deploy --stage dev
serverless deploy --stage prod