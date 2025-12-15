# UmiOCR 集成

## 概述

UmiOCR 是一个开源的离线 OCR 服务，已集成到本项目中。

## Docker 服务

```yaml
# docker-compose.yml
umiocr:
  image: eairship/umi-ocr:latest
  ports:
    - "1224:1224"
```

## 环境变量

```bash
UMIOCR_ENDPOINT=http://localhost:1224
UMIOCR_TIMEOUT=60
```

## 支持的引擎

- `paddleocr`: PaddleOCR（主要）
- `tesseract`: Tesseract（备用）
- `umiocr`: UmiOCR

## 语言支持

| 代码 | 语言 |
|------|------|
| ch / chi_sim | 简体中文 |
| eng / en | 英文 |
| chi_tra | 繁体中文 |
| jpn / japan | 日语 |
| kor / korean | 韩语 |
| rus | 俄语 |

## 使用方法

在规则配置中选择 `umiocr` 作为 OCR 引擎即可使用。

## 参考文档

- [UmiOCR HTTP 接口文档](https://github.com/hiroi-sora/Umi-OCR/blob/main/docs/http/README.md)
- [Docker 部署文档](https://github.com/hiroi-sora/Umi-OCR_runtime_linux/blob/main/README-docker.md)
