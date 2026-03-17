## seedream-5.0-lite-文生图

### 输入示例
```python
import os
# Install SDK:  pip install 'volcengine-python-sdk[ark]' .
from volcenginesdkarkruntime import Ark 

client = Ark(
    # The base URL for model invocation
    base_url="https://ark.cn-beijing.volces.com/api/v3", 
    # Get API Key：https://console.volcengine.com/ark/region:ark+cn-beijing/apikey
    api_key=os.getenv('ARK_API_KEY'), 
)
 
imagesResponse = client.images.generate( 
    # Replace with Model ID
    model="doubao-seedream-5-0-260128",
    prompt="充满活力的特写编辑肖像，模特眼神犀利，头戴雕塑感帽子，色彩拼接丰富，眼部焦点锐利，景深较浅，具有Vogue杂志封面的美学风格，采用中画幅拍摄，工作室灯光效果强烈。",
    size="2K",
    output_format="png",
    response_format="url",
    watermark=False
) 
 
print(imagesResponse.data[0].url)
```

### 输出示例
```json
{
    "model": "doubao-seedream-5-0-260128",
    "created": 1757321139,
    "data": [
        {
            "url": "https://...",
            "size": "3104x1312"
        }
    ],
    "usage": {
        "generated_images": 1,
        "output_tokens": xxx,
        "total_tokens": xxx
    }
}
```


## seedream-5.0-lite-图生图

### 输入示例
```python
import os
# Install SDK:  pip install 'volcengine-python-sdk[ark]'
from volcenginesdkarkruntime import Ark 

client = Ark(
    # The base URL for model invocation
    base_url="https://ark.cn-beijing.volces.com/api/v3", 
    # Get API Key：https://console.volcengine.com/ark/region:ark+cn-beijing/apikey
    api_key=os.getenv('ARK_API_KEY'), 
)
 
imagesResponse = client.images.generate( 
    # Replace with Model ID
    model="doubao-seedream-5-0-260128", 
    prompt="保持模特姿势和液态服装的流动形状不变。将服装材质从银色金属改为完全透明的清水（或玻璃）。透过液态水流，可以看到模特的皮肤细节。光影从反射变为折射。",
    image="https://ark-project.tos-cn-beijing.volces.com/doc_image/seedream4_5_imageToimage.png",
    size="2K",
    output_format="png",
    response_format="url",
    watermark=False
) 
 
print(imagesResponse.data[0].url)
```

### 输出示例
```json
{
    "model": "doubao-seedream-5-0-260128",
    "created": 1757323224,
    "data": [
        {
            "url": "https://...",
            "size": "1760x2368"
        }
    ],
    "usage": {
        "generated_images": 1,
        "output_tokens": 16280,
        "total_tokens": 16280
    }
}
```


## seedream-5.0-lite-多图融合

### 输入示例
```python
import os
# Install SDK:  pip install 'volcengine-python-sdk[ark]'
from volcenginesdkarkruntime import Ark 

client = Ark(
    # The base URL for model invocation
    base_url="https://ark.cn-beijing.volces.com/api/v3", 
    # Get API Key：https://console.volcengine.com/ark/region:ark+cn-beijing/apikey
    api_key=os.getenv('ARK_API_KEY'), 
) 
imagesResponse = client.images.generate( 
    # Replace with Model ID
    model="doubao-seedream-5-0-260128",
    prompt="将图1的服装换为图2的服装",
    image=["https://ark-project.tos-cn-beijing.volces.com/doc_image/seedream4_imagesToimage_1.png", "https://ark-project.tos-cn-beijing.volces.com/doc_image/seedream4_5_imagesToimage_2.png"],
    size="2K",
    sequential_image_generation="disabled",
    output_format="png",
    response_format="url",
    watermark=False
) 
 
print(imagesResponse.data[0].url)
```

### 输出示例
```json
import os
# Install SDK:  pip install 'volcengine-python-sdk[ark]'
from volcenginesdkarkruntime import Ark 

client = Ark(
    # The base URL for model invocation
    base_url="https://ark.cn-beijing.volces.com/api/v3", 
    # Get API Key：https://console.volcengine.com/ark/region:ark+cn-beijing/apikey
    api_key=os.getenv('ARK_API_KEY'), 
) 
imagesResponse = client.images.generate( 
    # Replace with Model ID
    model="doubao-seedream-5-0-260128",
    prompt="将图1的服装换为图2的服装",
    image=["https://ark-project.tos-cn-beijing.volces.com/doc_image/seedream4_imagesToimage_1.png", "https://ark-project.tos-cn-beijing.volces.com/doc_image/seedream4_5_imagesToimage_2.png"],
    size="2K",
    sequential_image_generation="disabled",
    output_format="png",
    response_format="url",
    watermark=False
) 
 
print(imagesResponse.data[0].url)
```


## seedream-5.0-lite-多参考图生组图

### 输入示例
```python
import os
# Install SDK:  pip install 'volcengine-python-sdk[ark]' .
from volcenginesdkarkruntime import Ark 
from volcenginesdkarkruntime.types.images.images import SequentialImageGenerationOptions

client = Ark(
    # The base URL for model invocation
    base_url="https://ark.cn-beijing.volces.com/api/v3", 
    # Get API Key：https://console.volcengine.com/ark/region:ark+cn-beijing/apikey
    api_key=os.getenv('ARK_API_KEY'), 
) 
 
imagesResponse = client.images.generate( 
    # Replace with Model ID
    model="doubao-seedream-5-0-260128",
    prompt="生成3张女孩和奶牛玩偶在游乐园开心地坐过山车的图片，涵盖早晨、中午、晚上",
    image=["https://ark-project.tos-cn-beijing.volces.com/doc_image/seedream4_imagesToimages_1.png", "https://ark-project.tos-cn-beijing.volces.com/doc_image/seedream4_imagesToimages_2.png"],
    size="2K",
    sequential_image_generation="auto",
    sequential_image_generation_options=SequentialImageGenerationOptions(max_images=3),
    output_format="png",
    response_format="url",
    watermark=False
) 
 
# Iterate through all image data
for image in imagesResponse.data:
    # Output the current image's URL and size
    print(f"URL: {image.url}, Size: {image.size}")
```

### 输出示例
```json
{
  "model": "doubao-seedream-5-0-260128",
  "created": 1757388756,
  "data": [
    {
      "url": "https://...",
      "size": "2720x1536"
    },
    {
      "url": "https://...",
      "size": "2720x1536"
    },
    {
      "url": "https://...",
      "size": "2720x1536"
    }
  ],
  "usage": {
    "generated_images": 3,
    "output_tokens": 48960,
    "total_tokens": 48960
  }
}
```


## seedream-5.0-lite-联网搜索

### 输入示例
```python
import os
# Install SDK:  pip install 'volcengine-python-sdk[ark]' .
from volcenginesdkarkruntime import Ark 
from volcenginesdkarkruntime.types.images.images import ContentGenerationTool

client = Ark(
    # The base URL for model invocation
    base_url="https://ark.cn-beijing.volces.com/api/v3", 
    # Get API Key：https://console.volcengine.com/ark/region:ark+cn-beijing/apikey
    api_key=os.getenv('ARK_API_KEY'), 
)

imagesResponse = client.images.generate(
    # Replace with Model ID
    model="doubao-seedream-5-0-260128",
    prompt="制作一张上海未来5日的天气预报图，采用现代扁平化插画风格，清晰展示每日天气、温度和穿搭建议。 整体为横向排版，标题为“上海未来5日天气预报”，包含5个等宽的垂直卡片，从左到右依次排列。 整体风格为现代、干净、友好的扁平化矢量插画风格，线条清晰，色彩柔和。人物形象采用年轻男女的卡通插画，表情自然，姿态放松，服装细节清晰。",
    size="2048x2048",
    output_format="png",
    response_format="url",
    tools=[ContentGenerationTool(type="web_search")],
    watermark=False,
    
)

print(imagesResponse.data[0].url)
```

### 输出示例
```json
{
    "model": "doubao-seedream-5-0-260128",
    "created": 1757321139,
    "data": [
        {
            "url": "https://...",
            "size": "3104x1312"
        }
    ],
    "usage": {
        "generated_images": 1,
        "output_tokens": xxx,
        "total_tokens": xxx,
        "tool_usage": {
            "web_search": 1 // 实际搜索次数
        }
    }
}
```