import aiohttp

# асинхронная функция для загрузки файла (в виде байтов) на x0.at и получения ссылки на него
async def upload_to_x0(file_bytes, filename, mime_type):
    from config import X0_UPLOAD_URL
    """Загружает байты на x0.at"""
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field("file", file_bytes, filename=filename, content_type=mime_type)
        async with session.post(X0_UPLOAD_URL, data=data) as response:
            if response.status != 200:
                return None
            return (await response.text()).strip()