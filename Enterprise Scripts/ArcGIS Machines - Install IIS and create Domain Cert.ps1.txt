function New-CertificateRequest {
    param ( [string]$hostname )
 
    $CATemplate = "WebServer"
    $CertificateINI = "cert.ini"
    $CertificateREQ = "cert.req"
    $CertificateRSP = "cert.rsp"
    $CertificateCER = "cert.cer"
    $Subject = 'Subject="CN=' + $hostname + '"'
    $FriendlyName = 'FriendlyName=' + $hostname
    $SAN = '_continue_ = "dns=' + $hostname + '&"'
 
    ### INI file generation
    new-item -type file $CertificateINI -force
    add-content $CertificateINI '[Version]'
    add-content $CertificateINI 'Signature="$Windows NT$"'
    add-content $CertificateINI ''
    add-content $CertificateINI '[NewRequest]'
    add-content $CertificateINI $Subject
    add-content $CertificateINI 'Exportable=TRUE'
    add-content $CertificateINI 'KeyLength=2048'
    add-content $CertificateINI 'KeySpec=1'
    add-content $CertificateINI 'KeyUsage=0xA0'
    add-content $CertificateINI 'MachineKeySet=True'
    add-content $CertificateINI 'ProviderName="Microsoft RSA SChannel Cryptographic Provider"'
    add-content $CertificateINI 'ProviderType=12'
    add-content $CertificateINI 'SMIME=FALSE'
    add-content $CertificateINI 'RequestType=PKCS10'
    add-content $CertificateINI $FriendlyName
    add-content $CertificateINI '[Strings]'
    add-content $CertificateINI 'szOID_ENHANCED_KEY_USAGE = "2.5.29.37"'
    add-content $CertificateINI 'szOID_PKIX_KP_SERVER_AUTH = "1.3.6.1.5.5.7.3.1"'
    add-content $CertificateINI 'szOID_PKIX_KP_CLIENT_AUTH = "1.3.6.1.5.5.7.3.2"'
    add-content $CertificateINI 'szOID_SUBJECT_ALT_NAME2 = "2.5.29.17"'
    add-content $CertificateINI '[Extensions]'
    add-content $CertificateINI '2.5.29.17 = "{text}"'
    add-content $CertificateINI $SAN

 
    ### Certificate request generation
    if (test-path $CertificateREQ) {del $CertificateREQ}
    certreq -new $CertificateINI $CertificateREQ
 
    ### Online certificate request and import
    if ($OnlineCA) {
        if (test-path $CertificateCER) {del $CertificateCER}
        if (test-path $CertificateRSP) {del $CertificateRSP}
        certreq -submit -attrib "CertificateTemplate:$CATemplate" -config $OnlineCA $CertificateREQ $CertificateCER
        certreq -accept $CertificateCER
    }
    
    ### Delete certificate request files
    if (test-path $CertificateINI) {del $CertificateINI}
    if (test-path $CertificateREQ) {del $CertificateREQ}
    if (test-path $CertificateRSP) {del $CertificateRSP}
    if (test-path $CertificateCER) {del $CertificateCER}
}

## Main
if ($args.length -ne 0) {$hostname = $args[0]}
else {$hostname = "$env:computername.$env:userdnsdomain".ToLower()}

# Check if a CA exists in the domain and if IIS is installed
if (@(certutil -dump | select-string "Config:")) {
    $OnlineCA = (certutil -dump | select-string "Config:")[-1].Line.replace("``",'"').replace("'",'"').split('"')[1]
} else {
    Write-Host "Unable to determine certificate authority (CA) for this domain"
    Exit
}
if (-not @(Get-Service W3SVC -ErrorAction Ignore)) {
	Install-WindowsFeature -name Web-Server -IncludeManagementTools
    Write-Host "IIS was not installed on this machine, but now is!"
    Exit
}

# Check if a certificate already exists and prompt user to overwrite
if (@(Get-ChildItem cert:\LocalMachine\My | where-object { $_.FriendlyName -eq "$hostname" }).count -ne 0) {
    Write-Host "A certificate for $hostname already exists"
    $reply = Read-Host -Prompt "Overwrite existing certificate? (y/n)"
    if ( $reply -notmatch "[yY]" ) { Exit }
    Get-ChildItem cert:\LocalMachine\My | where-object { $_.FriendlyName -eq "$hostname" } | Remove-Item
}
New-CertificateRequest -hostname $hostname > $null
Write-Host "`nCreated a new certificate for $hostname"

# Create https binding if necessary and add new cert to https binding
import-module WebAdministration
if (@(Get-WebBinding -name "Default Web Site" | Where-Object {$_.protocol -eq "https"}).count -eq 0) {
    New-WebBinding -name "Default Web Site" -Protocol https -Port 443
    Write-Host 'Created https binding for "Default Web Site"'
}
if (@(netsh http show sslcert ipport="0.0.0.0:443" | select-string -pattern "IP:port").count -ne 0) {
    netsh http delete sslcert ipport="0.0.0.0:443" > $null
}
$cert = (Get-ChildItem cert:\LocalMachine\My | where-object { $_.FriendlyName -eq "$hostname" } | Select-Object -First 1).Thumbprint
$guid = [guid]::NewGuid().ToString("B")
netsh http add sslcert ipport="0.0.0.0:443" certhash=$cert certstorename=MY appid="$guid" > $null
Write-Host "Updated https binding to use this certificate"

# Export certificate to .pfx (Windows 2016 and higher)
$scriptPath = split-path -parent $MyInvocation.MyCommand.Definition
if ([Environment]::OSVersion.Version -ge (new-object 'Version' 6,2)) {
    $pfxname = $hostname.Split(".")[0]
    if ($pfxname -eq '*') {$pfxname = "wildcard"}
    $pfxname = $pfxname + ".pfx"
    Remove-Item $scriptPath\$pfxname -ErrorAction Ignore
    $pfxpwd = ConvertTo-SecureString -String "certificate" -Force -AsPlainText
    $cert = (Get-ChildItem cert:\LocalMachine\My | where-object { $_.FriendlyName -eq "$hostname" } | Select-Object -First 1).Thumbprint
    Get-ChildItem -Path cert:\localMachine\My\$cert | Export-PfxCertificate -FilePath $scriptPath\$pfxname -Password $pfxpwd -ChainOption BuildChain > $null
    Write-Host "Exported certificate in PFX format with password 'certificate' to"
    Write-Host "    $scriptPath\$pfxname"
}

# Export domain CA root certificate to domainRoot.cer
Remove-Item $scriptPath\domainRoot.cer -ErrorAction Ignore
certutil -config $OnlineCA '-ca.cert' $scriptPath\domainRoot.cer > $null
Write-Host "Exported domain root certificate to"
Write-Host "    $scriptPath\domainRoot.cer"