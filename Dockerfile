FROM mcr.microsoft.com/playwright:focal

RUN useradd -ms /bin/bash crawler

USER crawler

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt


COPY mangaMetadata.py config_loader.py progress.py ./
COPY komga/ ./komga/
COPY sources/ ./sources/


CMD ["python", "-u", "mangaMetadata.py"]