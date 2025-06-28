
import sys
import os
sys.path.append("..")
from typing import List
from fastapi.responses import FileResponse
from fastapi import Query
from typing import Optional, List
from moviepy import VideoFileClip
import urllib.parse
# some reserved characters in the urls like # cannot be interpreted and so if file 
# name containing # is called via url it splits the name in the # and only the first part goes, 
# so we need to encode the reserved characters to be used in the urls.
# %23 is #
# %20 is space, etc
# so use urllib.parse

from pathlib import Path
from fastapi.responses import HTMLResponse
from fastapi import Request, HTTPException
from fastapi.responses import StreamingResponse
from starlette.status import HTTP_206_PARTIAL_CONTENT
from fastapi.responses import  StreamingResponse
from fastapi import FastAPI
from typing import Optional 

from fastapi import  APIRouter, Request, Response, Header
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
from multiprocessing import Process
import time

from concurrent.futures import ThreadPoolExecutor
import os




router = APIRouter(
    prefix="/apis",
    tags=["apis"],
    responses={401: {"user": "Not Authorised"}}
)

VIDEO_DIR = "../shared"
os.makedirs(VIDEO_DIR, exist_ok=True)

# hostname: str = "http://192.168.18.62:8000/apis/" # ubuntu server wifi ip
hostname: str = "http://192.168.1.10:8000/apis/"  #ubuntu server ethernet ip

class Item(BaseModel):
    name: str
    thumbnailUrl: str
    is_dir: bool

# Define the response model
class FileItem(BaseModel):
    name: str
    videoUrl: str
    thumbnailUrl: str
    is_dir: Optional[bool]

def create_thumbnail(video_path, output_path, time=1):
        clip = VideoFileClip(video_path)
        # Save a frame at `time` seconds
        frame = clip.get_frame(time)
        clip.save_frame(output_path, t=time)
        print(f"Thumbnail saved for: {video_path}")

def process_directory(video_dir, thumbnail_dir):
        if not os.path.exists(thumbnail_dir):
            os.makedirs(thumbnail_dir)

        # Step 1: Create or skip thumbnail for each video
        for filename in os.listdir(video_dir):
                if filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                    video_path = os.path.join(video_dir, filename)
                    thumbnail_filename = f"{os.path.splitext(filename)[0]}.jpg"
                    thumbnail_path = os.path.join(thumbnail_dir, thumbnail_filename)
                    
                    # ✅ Skip if thumbnail exists
                    if not os.path.exists(thumbnail_path):
                         create_thumbnail(video_path, thumbnail_path)
                           
        # Step 2: Delete thumbnails for missing video files
        for thumb_file in os.listdir(thumbnail_dir):
            try:
                if thumb_file.endswith(".jpg"):
                    video_name = os.path.splitext(thumb_file)[0]
                    video_exists = any(
                        os.path.exists(os.path.join(video_dir, f"{video_name}{ext}"))
                        for ext in ('.mp4', '.mov', '.avi', '.mkv')
                    )
                    if not video_exists:
                        os.remove(os.path.join(thumbnail_dir, thumb_file))
            except Exception as e:
                print(f"[Thumbnail Deletion Error] File: {thumb_file} - {e}")


@router.get("/listItems/{path:path}", response_model=List[Item])
def list_files(path: str):
    base_path = Path("../shared").resolve()  # Optional: restrict to a base folder
    target_path = (base_path / path).resolve()
    # print(target_path)

    # Security check: ensure target is inside base
    if not str(target_path).startswith(str(base_path)) or not target_path.is_dir():
        return []
    
    # Create thumbnails in: target_path / 'thumbnails'
    thumbnail_dir = target_path / "thumbnails"
    os.makedirs(thumbnail_dir, exist_ok=True)

    # Process thumbnails for video files. fire and forget process
    # thiss process will keep occupying resources if the process_directory() function hangs , especially when a bad unplayable video file is found.
    p = Process(target=process_directory, args=(str(target_path), str(thumbnail_dir)))
    p.daemon = True  # Dies with the parent process
    p.start()

    # print(str(Path(path)))
    # return [
    #     Item(name=entry.name, 
    #          thumbnailUrl=hostname+"getThumbnail/"+str(Path(path))+"/thumbnails/"+urllib.parse.quote(os.path.splitext(entry.name)[0] + ".jpg"), 
    #          is_dir=entry.is_dir())
    #     for entry in target_path.iterdir()
    #     if entry.name != "thumbnails"
    # ]

    return [
    Item(
        name=entry.name,
        thumbnailUrl=hostname + "getThumbnail/" + str(Path(path)) + "/thumbnails/" + urllib.parse.quote(os.path.splitext(entry.name)[0] + ".jpg"),
        is_dir=entry.is_dir()
    )
    for entry in sorted(
        target_path.iterdir(),
        key=lambda e: e.stat().st_mtime,
        reverse=True  # Most recent first
    )
    if entry.name != "thumbnails"
]


@router.get("/filenames/{path:path}", response_model=List[FileItem])
def list_files(path: str):
    base_path = Path("../shared").resolve()
    target_path = (base_path / str(Path(path).parent)).resolve()
    # Security check
    if not str(target_path).startswith(str(base_path)) or not target_path.is_dir():
        return []

    print("filenames path.name: ", str(Path(path).name))

    files = [
        FileItem(name=entry.name, videoUrl=hostname +"stream/" +str(Path(path).parent)+"/"+urllib.parse.quote(entry.name) , thumbnailUrl=hostname+"getThumbnail/"+str(Path(path).parent)+"/thumbnails/"+os.path.splitext(entry.name)[0] + ".jpg", is_dir=entry.is_dir())
        for entry in target_path.iterdir()
            if not entry.is_dir() and Path(path).name not in entry.name
    ] 

    # Create a FileItem instance
    item = FileItem(
    name=str(Path(path).name),
    videoUrl=hostname+"stream/"+str(Path(path).parent)+"/"+urllib.parse.quote(str(Path(path).name)),
    thumbnailUrl=hostname+"getThumbnail/"+str(Path(path))+"/thumbnails/"+urllib.parse.quote(os.path.splitext(str(Path(path).name))[0] + ".jpg"),
    is_dir=False
)

    # Add the item to the list
    files.insert(0, item)
    return  files


@router.get("/getThumbnail/{path:path}")
def get_thumbnail(path: str):
    base_path = Path("../shared").resolve()
    thumbnail_path = (base_path / path).resolve()

    if not thumbnail_path.exists() or not thumbnail_path.is_file():
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    return FileResponse(thumbnail_path, media_type="image/jpeg")

@router.get("/stream/{filename:path}")
def stream_video(filename: str, request: Request):
    # print("pathRaw:", filename)
    file_path = os.path.join(VIDEO_DIR, filename)
    # print("path:", file_path)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("range")

    if range_header is None:
        # If no range header, return full video
        def full_file():
            with open(file_path, "rb") as f:
                yield from f
        return StreamingResponse(
            full_file(),
            media_type="video/mp4",
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size),
            }
        )

    # Parse the range header
    bytes_range = range_header.replace("bytes=", "").split("-")
    start = int(bytes_range[0])
    end = int(bytes_range[1]) if bytes_range[1] else file_size - 1
    length = end - start + 1

    def range_file():
        with open(file_path, "rb") as f:
            f.seek(start)
            yield f.read(length)

    return StreamingResponse(
        range_file(),
        status_code=HTTP_206_PARTIAL_CONTENT,
        media_type="video/mp4",
        headers={
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(length),
        }
    )
    # print("pathRaw:", filename)
    file_path = os.path.join(VIDEO_DIR, filename)
    # print("path:", file_path)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("range")

    if range_header is None:
        # If no range header, return full video
        def full_file():
            with open(file_path, "rb") as f:
                yield from f
        return StreamingResponse(
            full_file(),
            media_type="video/mp4",
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size),
            }
        )

    # Parse the range header
    bytes_range = range_header.replace("bytes=", "").split("-")
    start = int(bytes_range[0])
    end = int(bytes_range[1]) if bytes_range[1] else file_size - 1
    length = end - start + 1

    def range_file():
        with open(file_path, "rb") as f:
            f.seek(start)
            yield f.read(length)

    return StreamingResponse(
        range_file(),
        status_code=HTTP_206_PARTIAL_CONTENT,
        media_type="video/mp4",
        headers={
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(length),
        }
    )