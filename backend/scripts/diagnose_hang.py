import asyncio
import os
import sys
import time
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("diagnose")

# Load environment variables
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(backend_dir, ".env")
load_dotenv(env_path)

async def test_db_connection():
    logger.info("Testing Database Connection...")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL not found in .env")
        return

    logger.info(f"Database URL found (masked): {database_url.split('://')[0]}://***")

    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        
        engine = create_async_engine(database_url, echo=True)
        
        logger.info("Engine created. Connecting...")
        async with engine.connect() as conn:
            logger.info("Connected. Executing SELECT 1...")
            await conn.execute(text("SELECT 1"))
            logger.info("SELECT 1 executed successfully.")
            
            # Test SELECT DATABASE() if MySQL
            if "mysql" in database_url:
                logger.info("Executing SELECT DATABASE()...")
                result = await conn.execute(text("SELECT DATABASE()"))
                db_name = result.scalar()
                logger.info(f"Current Database: {db_name}")
        
        await engine.dispose()
        logger.info("Database connection test PASSED.")
        
    except Exception as e:
        logger.error(f"Database connection test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

def test_paddleocr():
    logger.info("Testing PaddleOCR Initialization...")
    try:
        # Set env var as in the app
        os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
        
        logger.info("Importing PaddleOCR...")
        from paddleocr import PaddleOCR
        
        logger.info("Initializing PaddleOCR (this might take time)...")
        ocr = PaddleOCR(
            text_detection_model_name='PP-OCRv5_mobile_det',
            text_recognition_model_name='PP-OCRv5_mobile_rec',
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            show_log=True
        )
        logger.info("PaddleOCR initialized successfully.")
        
    except ImportError:
        logger.warning("PaddleOCR not installed or import failed.")
    except Exception as e:
        logger.error(f"PaddleOCR test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    logger.info("Starting Diagnosis...")
    
    # Test DB first
    await test_db_connection()
    
    # Test PaddleOCR (run in thread executor to simulate non-blocking if possible, but here we run sync to test blocking)
    # In the real app, it's run in executor.
    logger.info("Running PaddleOCR test in separate thread...")
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, test_paddleocr)
    
    logger.info("Diagnosis Complete.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Diagnosis interrupted by user.")
