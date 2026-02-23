# 🏦 Banco Distribuido

Proyecto académico para la materia **Sistemas Distribuidos**.

Este sistema simula un banco que permite:

- Transferencias internas (mismo banco)
- Transferencias externas (entre bancos distintos vía HTTP)
- Comunicación usando JSON
- Autenticación con roles (Administrador y Cliente)
- Historial de transacciones

---

# 🌐 Arquitectura

Cada banco:

- Funciona como una instancia independiente.
- Tiene su propia base de datos.
- Expone un endpoint HTTP para recibir transferencias externas.
- Se comunica mediante JSON.

No importa el lenguaje o base de datos del otro banco, mientras respete el contrato HTTP.

---

# 🔁 Tipos de Transferencia

## 1️⃣ Transferencia Interna

- Ocurre dentro del mismo banco.
- No utiliza HTTP.
- Se procesa directamente en la base de datos local.

## 2️⃣ Transferencia Externa

- Ocurre entre bancos distintos.
- Utiliza HTTP POST.
- Envía datos en formato JSON.
- Confirma o revierte la operación según la respuesta del banco destino.

---

# 🔌 Endpoint de Integración

## URL

POST /api/receive-transfer/

Ejemplo completo:

http://IP_DEL_BANCO:PUERTO/api/receive-transfer/

---

# 📦 Formato del JSON que se debe enviar

```json
{
  "banco_origen": "Nombre del Banco",
  "cuenta_destino": "NUMERO_CUENTA_DESTINO",
  "monto": 50000
}
```

## Campos

| Campo | Tipo   | Descripción                           |
|-------|--------|---------------------------------------|
| banco_origen | string | Nombre del banco que envía |
| cuenta_destino | string | Número de cuenta del banco receptor |
| monto | number | Monto a transferir |

---

# ✅ Respuesta Esperada

## ✔ Éxito (Status 200)

```json
{
  "status": "success",
  "message": "Transferencia recibida correctamente"
}
```

## ❌ Error lógico (Status 400 o 404)

```json
{
  "status": "error",
  "message": "Cuenta no encontrada"
}
```

## ❌ Error técnico (Status 500)

```json
{
  "status": "error",
  "message": "Descripción del error"
}
```

---

# 🔁 Lógica del Banco Origen

- Si recibe **200 OK** → confirma la transferencia.
- Si recibe **4xx o 5xx** → revierte la operación.
- Si hay error de conexión → revierte la operación.

---

# 🧪 Cómo Probar Manualmente

### Con curl

```bash
curl -X POST http://IP:PUERTO/api/receive-transfer/ \
-H "Content-Type: application/json" \
-d '{"banco_origen":"Banco A","cuenta_destino":"123123","monto":50000}'
```

### Con Postman

1. Método: POST  
2. URL: `http://IP:PUERTO/api/receive-transfer/`  
3. Body → raw → JSON  
4. Enviar el JSON correspondiente  

---

# ⚠️ Reglas Importantes

- No usar `localhost` si el banco debe recibir conexiones externas.
- Usar IP real o URL pública.
- Respetar exactamente el formato JSON.
- Responder con códigos HTTP correctos.

---

# 🔐 Seguridad (Modo Académico)

Este proyecto es académico, por lo tanto:

- No se implementa autenticación en la API externa.
- No se implementa encriptación real.
- No se utiliza HTTPS obligatorio.
- No se implementa firma digital.

---

# 📊 Funcionalidades Implementadas

- Login con roles  
- Dashboard Administrador  
- Dashboard Cliente  
- Transferencia interna  
- Transferencia externa vía HTTP  
- Historial de transacciones  
- Control básico de saldo  

---

# 🎓 Conceptos de Sistemas Distribuidos Aplicados

- Sistemas autónomos  
- Comunicación cliente-servidor  
- Interoperabilidad entre lenguajes  
- Contrato común basado en JSON  
- Manejo de errores distribuidos  

---

Proyecto desarrollado con fines académicos.
