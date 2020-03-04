### 视频地址解析

两个接口

`/video/<string:vid>.json` 适合长缓存

`/video/<string:vid>/<int:itag>.json` 适合短缓存

部署于gae

`pip install -t lib -r requirements.txt && gcloud app deploy`


