import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def autenticar():
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

def extraer_cuerpo(payload):
    cuerpo = ""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data', '')
                if data:
                    cuerpo = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    break
    else:
        data = payload['body'].get('data', '')
        if data:
            cuerpo = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    return cuerpo

def obtener_newsletters(max_correos=5):
    creds = autenticar()
    service = build('gmail', 'v1', credentials=creds)

    query = 'from:(alphasignal.ai OR tldrnewsletter.com) newer_than:7d'

    resultado = service.users().messages().list(
        userId='me',
        q=query,
        maxResults=max_correos
    ).execute()

    mensajes = resultado.get('messages', [])

    if not mensajes:
        print("No se encontraron newsletters recientes.")
        return []

    correos = []
    for msg in mensajes:
        detalle = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='full'
        ).execute()

        headers = detalle['payload']['headers']
        asunto = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Sin asunto')
        remitente = next((h['value'] for h in headers if h['name'] == 'From'), '')
        cuerpo = extraer_cuerpo(detalle['payload'])

        correos.append({
            'asunto': asunto,
            'remitente': remitente,
            'cuerpo': cuerpo[:3000]
        })
        print(f"Encontrado: {asunto}")

    return correos

if __name__ == '__main__':
    newsletters = obtener_newsletters(max_correos=3)
    for i, correo in enumerate(newsletters, 1):
        print(f"\n--- Correo {i} ---")
        print(f"Asunto: {correo['asunto']}")
        print(f"Inicio del cuerpo:\n{correo['cuerpo'][:300]}")