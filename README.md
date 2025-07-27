# Adobe India Hackathon 2025: Connecting the Dots

This repository contains the solution for **Round 1** of the Adobe India Hackathon **"Connecting the Dots"**.  
The project is divided into two parts:

- **Round 1a**: A structural outline extractor for PDF documents.  
- **Round 1b**: A persona-driven document intelligence system.

---

## 🧠 Approach

### 📄 Round 1a: Document Outline Extraction

The primary challenge in Round 1a is to extract a **hierarchical outline** (Title, H1, H2, H3) from a PDF document.  
A simple approach based on font sizes is unreliable and discouraged.

#### ✅ Our Approach:
A **rule-based system** that analyzes various text features to identify headings.

#### 🔍 Text Extraction:
- We use **PyMuPDF (`fitz`)** for efficient extraction of text blocks and their properties.
- Chosen for its **speed and precision**, critical for the **10-second limit** on a 50-page PDF.
- Extracted properties include:
  - Text content
  - Font size
  - Font name
  - Coordinates

#### ⚙️ Feature Engineering:
For each text block, we analyze:
- **Font Weight**: Bold text suggests headings.
- **Font Size**: Larger fonts often indicate headings.
- **Line Spacing**: Headings usually have more spacing above/below.
- **Text Length**: Headings are typically shorter.
- **Numbering**: Patterns like `1.1`, `A.`, `i.` are strong heading indicators.

#### 🧠 Heading Classification Rules:
- The first prominent, largest-font block is marked as **Title**.
- Large, bold blocks → **H1**
- Smaller but structured/indented blocks → **H2/H3**

#### 🧾 JSON Output:
Identified headings are returned in a structured JSON format:
- `level` (Title, H1, H2, H3)
- `text`
- `page number`

> ✅ This avoids hardcoding and ensures generalizability + speed.

---

### 👤 Round 1b: Persona-Driven Document Intelligence

Round 1b builds on the structured output of Round 1a.  
Goal: extract and rank sections from documents based on a **persona** and their **"job-to-be-done"**.

#### 📚 Strategy:

- **Text Chunking**: Use the extracted outline (Title/H1/H2/H3) to break the document into meaningful sections.
- **Embedding Generation**: 
  - Use `sentence-transformers` (e.g., `all-MiniLM-L6-v2`)
  - Convert job description and text chunks into vector embeddings
  - Ensures semantic representation within **1GB model limit**
- **Relevance Scoring**:
  - Compute **cosine similarity** between persona embedding and section embeddings.
  - Higher score = more relevant to persona's task
- **Ranking**:
  - Rank all sections by relevance score
  - Top-ranked ones fulfill the `"Importance_rank"` requirement
- **Sub-section Analysis**:
  - For top sections, do fine-grained text analysis
  - Provide detailed insights as per problem statement

> 🔄 Generalizable across documents, personas, and use cases.

---

## ⚙️ How to Build and Run the Solution

The solution is **containerized with Docker** for ease of deployment and testing.

### ✅ Prerequisites
- Docker installed on your system.


🧩 Models and Libraries Used
PyMuPDF (fitz)
For fast and accurate PDF parsing with font and layout information.

sentence-transformers
For generating semantic embeddings in Round 1b (all-MiniLM-L6-v2 used).

numpy
For efficient numerical computations during scoring and ranking.

🔒 All components were built with performance, generality, and container-based reproducibility in mind, ensuring a robust submission for Adobe India Hackathon 2025.

vbnet
