import oss2
import urllib.parse

region = ''
endpoint = ''


geocloud_accessKeyId = ""
geocloud_accessKeySecret = ""
geocloud_bucket_name = ''
geocloud_auth = oss2.Auth(geocloud_accessKeyId, geocloud_accessKeySecret)
geocloud_bucket = oss2.Bucket(geocloud_auth, endpoint, geocloud_bucket_name, region=region)


aster_accessKeyId = ""
aster_accessKeySecret = ""
aster_bucket_name = ''
aster_auth = oss2.Auth(aster_accessKeyId, aster_accessKeySecret)
aster_bucket = oss2.Bucket(aster_auth, endpoint, aster_bucket_name)


download_accessKeyId = ''
download_accessKeySecret = ''
download_bucket_name = ''
download_auth = oss2.Auth(download_accessKeyId, download_accessKeySecret)
download_bucket = oss2.Bucket(download_auth, endpoint, download_bucket_name, region=region)


upload_accessKeyId = ""
upload_accessKeySecret = ""
upload_bucket_name = ''
upload_auth = oss2.Auth(upload_accessKeyId, upload_accessKeySecret)
upload_bucket = oss2.Bucket(upload_auth, endpoint, upload_bucket_name, region=region)



center_accessKeyId = ""
center_accessKeySecret = ""
center_bucket_name = ''
center_auth = oss2.Auth(center_accessKeyId, center_accessKeySecret)
center_bucket = oss2.Bucket(center_auth, endpoint, center_bucket_name, region=region)

