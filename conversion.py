import subprocess
import os
import shutil
import uuid
import time
import platform
import logging
from database import create_file_record

# Special library for high-quality PDF to Word conversion
try:
    from pdf2docx import Converter
except ImportError:
    Converter = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("conversion")

FORMAT_MAP = {
    "pdf": ["docx", "odt", "rtf", "txt", "html"],
    "doc": ["pdf", "odt", "rtf", "txt", "html"],
    "docx": ["pdf", "odt", "rtf", "txt", "html"],
    "odt": ["pdf", "docx", "rtf", "txt", "html"],
    "rtf": ["pdf", "docx", "odt", "txt", "html"],
    "txt": ["pdf", "docx", "odt", "rtf", "html"],
    "html": ["pdf", "docx", "odt", "rtf", "txt"],
    "ppt": ["pdf", "docx", "odt", "pptx"],
    "pptx": ["pdf", "docx", "odt", "ppt"],
    "jpg": ["pdf"],
    "jpeg": ["pdf"],
    "png": ["pdf"],
}

MIME_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "doc": "application/msword",
    "odt": "application/vnd.oasis.opendocument.text",
    "rtf": "application/rtf",
    "txt": "text/plain",
    "html": "text/html",
    "ppt": "application/vnd.ms-powerpoint",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
}

def get_libreoffice_path():
    env_path = os.getenv("LIBREOFFICE_PATH")
    if env_path and os.path.exists(env_path):
        return env_path
    
    if platform.system() == "Windows":
        paths = [
            os.path.join(os.environ.get("PROGRAMFILES", "C:\\Program Files"), "LibreOffice", "program", "soffice.exe"),
            os.path.join(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"), "LibreOffice", "program", "soffice.exe"),
            "C:\\Program Files\\LibreOffice\\program\\soffice.exe",
        ]
        for p in paths:
            if os.path.exists(p):
                return p
        return "soffice"
    elif platform.system() == "Darwin":
        return "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    return "libreoffice"

async def convert_file(file_record, target_format):
    source_format = file_record["format"].lower()
    target = target_format.lower()
    
    input_path = os.path.abspath(file_record["stored_path"])
    if not os.path.exists(input_path):
        return {"success": False, "error": "Source file not found"}

    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    new_filename = f"{uuid.uuid4()}.{target}"
    permanent_path = os.path.join(uploads_dir, new_filename)

    # --- Choice A: PDF to DOCX using pdf2docx (Best Quality & No Errors) ---
    if source_format == "pdf" and target == "docx" and Converter:
        try:
            logger.info(f"Starting high-quality PDF to DOCX conversion using pdf2docx")
            cv = Converter(input_path)
            cv.convert(permanent_path)
            cv.close()
            
            return await finalize_conversion(file_record, target, permanent_path, new_filename)
        except Exception as e:
            logger.error(f"pdf2docx conversion failed: {str(e)}")
            # Fallback to LibreOffice if pdf2docx fails

    # --- Choice B: Everything else using LibreOffice ---
    # Prepare Work Dir
    work_dir = os.path.join(os.environ.get("TEMP", "/tmp"), f"conv-{uuid.uuid4().hex[:8]}")
    os.makedirs(work_dir, exist_ok=True)
    
    input_ext = os.path.splitext(input_path)[1]
    work_input = os.path.join(work_dir, f"in{input_ext}")
    shutil.copy2(input_path, work_input)

    soffice = get_libreoffice_path()
    soffice_dir = os.path.dirname(soffice)
    
    # Improved profile path for Windows
    profile_dir = os.path.join(work_dir, "profile")
    p_dir = profile_dir.replace("\\", "/")
    if ":" in p_dir and not p_dir.startswith("/"):
        p_dir = "/" + p_dir
    profile_url = "file://" + p_dir
    
    env = os.environ.copy()
    if platform.system() == "Windows" and os.path.exists(soffice_dir):
        env["PATH"] = soffice_dir + os.pathsep + env.get("PATH", "")

    args = [
        soffice,
        "--headless",
        f"-env:UserInstallation={profile_url}",
        "--convert-to",
        target,
        "--outdir",
        work_dir,
        work_input,
    ]

    try:
        logger.info(f"Running LibreOffice conversion: {' '.join(args)}")
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        stdout, stderr = process.communicate()
        
        output_path = None
        for _ in range(15):
            time.sleep(1)
            files = os.listdir(work_dir)
            for f in files:
                if f.lower().endswith(f".{target}") and f.lower() != f"in{input_ext}".lower():
                    output_path = os.path.join(work_dir, f)
                    break
            if output_path:
                break
        
        if not output_path:
            return {"success": False, "error": f"LibreOffice failed to produce output. Logs: {stderr or stdout}"}

        shutil.move(output_path, permanent_path)
        return await finalize_conversion(file_record, target, permanent_path, new_filename)

    except Exception as e:
        logger.error(f"LibreOffice conversion failed: {str(e)}")
        return {"success": False, "error": str(e)}
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

async def finalize_conversion(file_record, target, permanent_path, new_filename):
    # Original name with new extension
    original_base = os.path.splitext(file_record["original_name"])[0]
    output_display_name = f"{original_base}.{target}"
    
    # Create DB record
    new_record = create_file_record({
        "filename": new_filename,
        "original_name": output_display_name,
        "stored_path": permanent_path,
        "mime_type": MIME_TYPES.get(target, "application/octet-stream"),
        "size": os.path.getsize(permanent_path),
        "format": target
    })
    
    return {"success": True, "id": new_record["id"], "filename": new_record["original_name"]}
