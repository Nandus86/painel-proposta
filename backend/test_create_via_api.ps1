$body = @{email='teste@teste.com'; senha='admin123'} | ConvertTo-Json
$login = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" -Method Post -Body $body -ContentType "application/json"
$token = $login.access_token
Write-Host "Got token, creating user..."

$headers = @{ Authorization = "Bearer $token" }
$userBody = @{
    nome = 'Novo Usuario Teste'
    email = 'novo_api_' + [guid]::NewGuid().ToString("N").Substring(0,6) + '@teste.com'
    cargo = 'Vendedor'
    telefone = '(11)99999-9999'
    role = 'vendedor'
    senha = 'test123'
} | ConvertTo-Json

try {
    $r = Invoke-RestMethod -Uri "http://localhost:8000/api/usuarios" -Method Post -Body $userBody -ContentType "application/json" -Headers $headers
    $r | ConvertTo-Json -Depth 3
} catch {
    $_.Exception.Response.StatusCode.value__
    $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
    $reader.ReadToEnd()
}
