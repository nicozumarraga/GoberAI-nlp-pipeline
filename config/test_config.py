import os
import dotenv

dotenv.load_dotenv('config/.env')

# PDF URLs to test
PDF_URLS = [
    "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?DocumentIdParam=cGvQdaF/qmEnKvN211kkZep9eLYPa5sPlu0VFp1fA/h5Fg1pTaKl4FN73msJksylIVq1IvdI5PofzpP36PwDr6Jmx2BDu2S/t4P9dvlPFULfdyQgZAdTm3EfcUAC7CJ6&cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D",
    "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?DocumentIdParam=MyaCN+DaUlHho/5clqwQNcpdhhqLGFdIPSQT8pnyitW170n/GQQs29amlMG4xs7iKR6ulnqEOIut1Ovlt2H4ixgpNv1ZzW0m6XACjA2Wu/PVTD3T98KC0nSgQFM0q+5s&cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D",
    "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?DocumentIdParam=z/ghU5864J3UKnVAwwWNrCp9Nvi9o32DrO2HfqSQ/7y0QPTDGl+TgSxAzGaBF9hR0w94oIWtN2EkYA0Og4DmgZLmV7aY3ZdlQ8+xtPvjDpeB0nvVKRzfe4rpHcnlPhSZ&cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D",
    "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?DocumentIdParam=8hgVPRbuSgXhyguKtFy5AiXeHvokF+2dllmtzd8sapWTAcvE3IDVxGhRuhi9GWXq2A4V3aEdzAqu7KG6zJkIGd4Rr6XPeaqztAIX1SSQM+2B0nvVKRzfe4rpHcnlPhSZ&cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D",
    "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?DocumentIdParam=wpL05Sv0vuASNVV59os02t1zLXzhEwhUpVrAmIiI4w+06WPE0AvLvdg6w0OZqYyrGivKjCsC2R7gEgBRON2aZeZ1y1C5nSiBmcFaXawL1GJt/o8fNevwsujgRzaBbugn&cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D",
    ""
]

PDF_FILE_NAMES = [
    "data/raw_pdfs/DOC_CD2024-001193614.pdf",
    "data/raw_pdfs/DOC_CN2024-001193585.pdf",
    "data/raw_pdfs/DOC20241111091415Pliego_de_prescripciones_tecnicas.pdf",
    "data/raw_pdfs/DOC20241111092201Pliego_de_clausulas_administrativas.pdf",
    "data/raw_pdfs/DOC20241111092201Pliego_de_clausulas_administrativas2.pdf"
]

MARKDOWN_FILE_NAMES = [
    "data/markdown/PCAP Coor POB.md"
]



QUESTIONS = [
    """
PLANTILLA DE RESUMEN DE INFORMACIÓN PARA LICITACIONES PÚBLICAS
1. INFORMACIÓN GENERAL DEL PROYECTO
Nombre del proyecto: [Nombre completo de la licitación]
Código o referencia de licitación: [Código de identificación]
Entidad convocante: [Organismo que publica la licitación]
Objeto de la licitación: [Descripción breve del servicio/producto a contratar]
Plazo de presentación de ofertas: [Fecha límite de presentación]
""",
"""
2. ASPECTOS ECONÓMICOS Y FINANCIEROS
Solvencia Económica y Financiera
Requisitos básicos: [Especificar si se exige solvencia económica y financiera o si está eximida]
Documentación necesaria: [Declaraciones, certificados u otros documentos requeridos]
Otros comentarios relevantes: [Ejemplo: Se requiere/no se requiere garantía provisional o definitiva]
Presupuesto Base de Licitación
Importe total: [Monto total, especificando si incluye impuestos]
Condiciones económicas: [Forma de distribución del presupuesto]
Desglose por lotes:
Lote 1: [Descripción + Importe]
Lote 2: [Descripción + Importe]
Modificaciones presupuestarias: [Condiciones bajo las cuales se puede modificar el presupuesto]
Garantía Definitiva
Importe de la garantía: [Monto requerido o exención]
Condiciones de devolución: [Si aplica]
Documentación requerida: [Si aplica]
""",
"""
3. ASPECTOS TÉCNICOS
Plazo de Ejecución
Duración del contrato: [Fecha de inicio y finalización]
Condiciones especiales: [Requisitos específicos sobre plazos de entrega]
Solvencia Técnica o Profesional
Requisitos de experiencia o certificaciones: [Si es aplicable]
Documentación necesaria: [Declaraciones responsables u otros documentos]
Especificaciones del Producto o Servicio
Descripción de especificaciones técnicas requeridas:
Lote 1: [Detalles técnicos]
Lote 2: [Detalles técnicos]
Normativas o estándares a cumplir: [Normas específicas aplicables]
Plazos de entrega y transporte:
Suministro normal: [Días hábiles]
Suministro urgente: [Horas o días, si aplica]
""",
"""
4. CONDICIONES CONTRACTUALES
Condiciones de Ejecución Especiales
Requisitos adicionales durante la ejecución: [Ejemplo: garantías de calidad, plazos de sustitución de productos defectuosos]
Modificación del Contrato
Posibilidad de modificaciones: [Sí/No y condiciones]
Procedimiento para solicitar modificaciones: [Cómo se deben solicitar y aprobar]
Facturación y Condiciones de Pago
Procedimiento de facturación: [Sistema de presentación de facturas]
Condiciones de pago: [Plazo y entidad responsable]
Entidades responsables del pago: [Nombre del organismo que gestiona el pago]
""",
"""
5. CRITERIOS DE ADJUDICACIÓN
Criterios de valoración de las ofertas: [Criterios principales: económicos, técnicos, sociales, etc.]
Ponderación de los criterios: [Distribución de puntos o porcentaje]
Comentarios adicionales sobre la evaluación: [Criterios de desempate u otros factores]
6. OTROS COMENTARIOS Y RECOMENDACIONES
Comentarios generales sobre la licitación: [Consideraciones clave, restricciones o aspectos legales relevantes]
Observaciones sobre otros apartados del pliego: [Detalles adicionales que deben tener en cuenta los licitadores]
7. DOCUMENTACIÓN ADICIONAL NECESARIA
Lista de documentos requeridos para la presentación de la oferta:
[Documento 1]
[Documento 2]
[Documento 3]
Fuente de los documentos: [Referencia al pliego de cláusulas administrativas y prescripciones técnicas]
"""
]

# Pipeline configuration
OUTPUT_DIR = "results"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
EMBEDDING_MODEL = ""

# API keys
MARKER_API = os.getenv("MARKER_API")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_AI_API = os.getenv("GOOGLE_AI_API")

# LLM config
LLM_MODEL = "deepseek-chat"
LLM_TEMPERATURE = 0.2

# Logging configuration
ENABLE_LOGGING = True
LOG_LEVEL = "INFO"
