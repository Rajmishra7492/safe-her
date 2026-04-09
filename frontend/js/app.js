const API_BASE="http://127.0.0.1:5000";const qs=(s)=>document.querySelector(s);let token=localStorage.getItem("token")||"";let user=JSON.parse(localStorage.getItem("user")||"null");let loc=null;const show=(el,msg,b=false)=>{el.textContent=msg;el.style.color=b?"#dc2626":"#10b981"};const setAuth=(ok)=>{qs("#authSection").classList.toggle("hidden",ok);qs("#dashboardSection").classList.toggle("hidden",!ok);if(ok&&user?.is_admin)qs("#adminPanel").classList.remove("hidden")};const save=(t,u)=>{token=t;user=u;localStorage.setItem("token",t);localStorage.setItem("user",JSON.stringify(u));setAuth(true)};const clear=()=>{token="";user=null;localStorage.clear();setAuth(false)};async function req(path,opt={}){const h=opt.headers||{};if(token)h.Authorization=`Bearer ${token}`;const r=await fetch(API_BASE+path,{...opt,headers:h});const d=await r.json();if(!r.ok)throw new Error(d.error||"Request failed");return d}function getLocation(){return new Promise((res,rej)=>navigator.geolocation.getCurrentPosition(p=>{loc={latitude:p.coords.latitude,longitude:p.coords.longitude};qs("#locationText").textContent=`Lat: ${loc.latitude.toFixed(5)}, Lng: ${loc.longitude.toFixed(5)}`;const b=`${loc.longitude-0.01},${loc.latitude-0.01},${loc.longitude+0.01},${loc.latitude+0.01}`;qs("#mapFrame").src=`https://www.openstreetmap.org/export/embed.html?bbox=${b}&layer=mapnik&marker=${loc.latitude},${loc.longitude}`;res(loc)},()=>rej(new Error("Unable to fetch location")))}
qs("#showLogin").onclick=()=>{qs("#loginForm").classList.add("active");qs("#registerForm").classList.remove("active");qs("#showLogin").classList.add("active");qs("#showRegister").classList.remove("active")};
qs("#showRegister").onclick=()=>{qs("#registerForm").classList.add("active");qs("#loginForm").classList.remove("active");qs("#showRegister").classList.add("active");qs("#showLogin").classList.remove("active")};
qs("#registerForm").onsubmit=async(e)=>{e.preventDefault();try{const d=await req("/register",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:qs("#registerName").value,email:qs("#registerEmail").value,password:qs("#registerPassword").value})});save(d.token,d.user);show(qs("#authMessage"),"Registered") }catch(err){show(qs("#authMessage"),err.message,true)}};
qs("#loginForm").onsubmit=async(e)=>{e.preventDefault();try{const d=await req("/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:qs("#loginEmail").value,password:qs("#loginPassword").value})});save(d.token,d.user);show(qs("#authMessage"),"Login successful") }catch(err){show(qs("#authMessage"),err.message,true)}};
qs("#trackLocationBtn").onclick=async()=>{try{await getLocation()}catch(e){alert(e.message)}};
qs("#sosBtn").onclick=async()=>{try{const c=loc||await getLocation();const d=await req("/sos",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(c)});alert(`${d.message}. Notified contacts: ${d.notified_contacts}`);loadAlerts()}catch(e){alert(e.message)}};
qs("#contactForm").onsubmit=async(e)=>{e.preventDefault();try{await req("/add-contact",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:qs("#contactName").value,phone:qs("#contactPhone").value,relation:qs("#contactRelation").value})});alert("Contact added");e.target.reset()}catch(err){alert(err.message)}};
qs("#incidentForm").onsubmit=async(e)=>{e.preventDefault();try{const c=loc||await getLocation();const fd=new FormData();fd.append("description",qs("#incidentDescription").value);fd.append("location",qs("#incidentLocation").value);fd.append("latitude",c.latitude);fd.append("longitude",c.longitude);const f=qs("#incidentImage").files[0];if(f)fd.append("image",f);const r=await fetch(API_BASE+"/report-incident",{method:"POST",headers:{Authorization:`Bearer ${token}`},body:fd});const d=await r.json();if(!r.ok)throw new Error(d.error||"Unable");show(qs("#riskResult"),`Risk Score: ${d.risk_analysis.risk_score}`);e.target.reset();loadAlerts()}catch(err){show(qs("#riskResult"),err.message,true)}};
async function loadAlerts(){try{const d=await req("/get-alerts");qs("#alertsList").innerHTML=d.alerts.length?d.alerts.map(a=>`<li>[${a.type}] ${a.message} (${a.created_at})</li>`).join(""):"<li>No alerts found.</li>"}catch(e){qs("#alertsList").innerHTML=`<li>${e.message}</li>`}}
qs("#loadAlertsBtn").onclick=loadAlerts;qs("#loadAdminBtn").onclick=async()=>{try{qs("#adminData").textContent=JSON.stringify(await req("/admin/analytics"),null,2)}catch(e){qs("#adminData").textContent=e.message}};qs("#logoutBtn").onclick=clear;qs("#themeToggle").onclick=()=>document.body.classList.toggle("dark");if(token&&user){setAuth(true);loadAlerts()}else setAuth(false);
 async function sendLocationSMS() {
        try {
            // Check if we have an emergency contact
            if (!emergencyContact) {
                // If no contact is saved, try to open SMS app with just the message
                showMessage('No emergency contact saved. Opening SMS app with a generic message.', 'info');
            }
            
            // Try to get user's location
            let location = null;
            try {
                location = await getUserLocation();
            } catch (error) {
                console.error('Error getting location for SMS:', error);
                // If location fails, show an alert and continue with a generic message
                showError('Could not access your location. A generic emergency SMS will be sent instead.');
            }
            
            // Create SMS content
            let message = '🚨 Emergency Alert!';
            
            // Add location link if available
            if (location && location.latitude && location.longitude) {
                const mapsLink = `https://maps.google.com/?q=${location.latitude},${location.longitude}`;
                message += ` My location: ${mapsLink}`;
            } else {
                message += ' I need help! (Location unavailable)';
            }
            
            // Create SMS URI with encoded message
            const encodedMessage = encodeURIComponent(message);
            
            // Construct SMS URI based on device platform and contact availability
            let smsUri;
            
            if (isAndroidDevice()) {
                // Android SMS format with semicolon for compatibility with more Android devices
                smsUri = emergencyContact 
                    ? `sms:${emergencyContact};?body=${encodedMessage}` 
                    : `sms:;?body=${encodedMessage}`;
            } else {
                // iOS and other platforms format
                smsUri = emergencyContact 
                    ? `sms:${emergencyContact}?body=${encodedMessage}` 
                    : `sms:?body=${encodedMessage}`;
            }
            
            // Open SMS app
            window.open(smsUri, '_blank');
            
            // Show success message
            if (location && location.latitude && location.longitude) {
                showMessage('SMS app opened with your current location.', 'success');
            } else {
                showMessage('SMS app opened with a generic emergency message.', 'info');
            }
            
            return true;
        } catch (error) {
            console.error('Error sending SMS:', error);
            showError('Could not open SMS app. Please manually send a message to your emergency contact.');
            return false;
        }
    }