console.log('main.js loaded');
document.addEventListener('DOMContentLoaded', ()=>{
  console.log('DOMContentLoaded - attaching upload-form listeners');
  // upload forms with real-time feedback
  document.querySelectorAll('.upload-form').forEach(form=>{
    const moduleName = form.dataset.module || 'unknown';
    console.log('Attaching submit listener for module:', moduleName, form);
    form.addEventListener('submit', async (e)=>{
      e.preventDefault();
      const module = form.dataset.module;
      const fileInput = form.querySelector('input[type=file]');
      // `.result` sits outside the <form> as a sibling inside the same module card.
      // Use closest('.module') then querySelector to robustly find it and avoid null.
      const container = form.closest('.module') || form.parentElement;
      const resultEl = container ? container.querySelector('.result') : null;
      
      if(!fileInput.files.length) {
        resultEl.innerHTML = '<div class="alert alert-warning fade-in">📁 Please select file(s)</div>';
        return;
      }
      
      const fileCount = fileInput.files.length;
      const fileNames = Array.from(fileInput.files).map(f => f.name).join(', ');
      
      // Show loading with details inside the module and also show full-screen overlay for better feedback
      if(resultEl){
        resultEl.innerHTML = `
          <div class="alert alert-info fade-in">
            <strong>⏳ Processing...</strong>
            <br><small style="font-size:0.85em;color:var(--muted);">
              Module: <strong>${module.toUpperCase()}</strong> &nbsp;•&nbsp; Files: <strong>${fileCount}</strong>
            </small>
          </div>
        `;
      }

      // Create or show processing overlay
      let overlay = document.querySelector('.processing-overlay');
      if(!overlay){
        overlay = document.createElement('div');
        overlay.className = 'processing-overlay';
        overlay.innerHTML = `
          <div class="processing-card">
            <div class="processing-header">
              <div class="processing-spinner">⏳</div>
              <div class="processing-info">
                <h4>Processing</h4>
                <p class="processing-desc">Preparing analysis...</p>
              </div>
            </div>
            <div class="processing-progress">
              <div class="progress"><div class="progress-bar" style="width:0%;background:linear-gradient(90deg,var(--accent),var(--accent-2));">0%</div></div>
              <p class="processing-note">This may take a few seconds for the first run.</p>
            </div>
          </div>
        `;
        document.body.appendChild(overlay);
      }
      overlay.classList.add('show');
      // update overlay text
      overlay.querySelector('.processing-desc').textContent = `Module: ${module.toUpperCase()} — Files: ${fileCount} (${fileNames})`;
      const progressBar = overlay.querySelector('.progress-bar');
      if(progressBar){ progressBar.style.width = '10%'; progressBar.textContent = 'Starting...'; }
      
      try{
        console.log(`Uploading ${fileCount} file(s) to /upload/${module}`);
        
        // Create form data with multiple files
        const fd = new FormData();
        for(let i = 0; i < fileInput.files.length; i++){
          if(module === 'duplicate' || module === 'image'){
            fd.append('files', fileInput.files[i]);
          } else {
            fd.append('file', fileInput.files[i]);
          }
        }
        
        const res = await fetch(`/upload/${module}`, { method:'POST', body: fd });
        const j = await res.json();
        
        console.log('Response:', j);
        
        // Update overlay progress to 90%
        const overlay = document.querySelector('.processing-overlay');
        if(overlay){
          const pb = overlay.querySelector('.progress-bar');
          if(pb){ pb.style.width = '90%'; pb.textContent = j.score ? `${j.score}%` : 'Finalizing...'; }
        }
        
        if(j.status === 'failed' || j.result === 'ERROR'){
          if(resultEl){
            resultEl.innerHTML = `
              <div class="alert alert-danger fade-in">
                <strong>❌ Analysis Failed</strong>
                <br>${j.message || j.error || 'Unknown error'}
              </div>
            `;
          }
          // show overlay error state then hide
          if(overlay){ overlay.querySelector('.processing-desc').textContent = 'Analysis failed'; overlay.classList.remove('show'); }
          return;
        }
        
        // Success result
        const resultColor = j.score > 70 ? 'success' : (j.score > 40 ? 'warning' : 'danger');
        
        // Determine icon based on result
        let icon = '📊';
        if(j.result.includes('AI') || j.result.includes('GENERATED')) icon = '🤖';
        if(j.result.includes('HUMAN')) icon = '👤';
        if(j.result.includes('UNIQUE')) icon = '✓';
        if(j.result.includes('REAL')) icon = '📸';
        if(j.result.includes('DUPLICATE')) icon = '⚠️';
        
        if(resultEl){
          resultEl.innerHTML = `
            <div class="alert alert-${resultColor} fade-in">
              <h5>${icon} <strong>${j.result}</strong></h5>
              <div style="margin-top:10px;">
                <div class="progress" style="height:25px;margin-bottom:10px;">
                  <div class="progress-bar bg-secondary" style="width:${j.score}%;display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;">
                    ${j.score}%
                  </div>
                </div>
                <p style="margin:0;"><small><strong>Files analyzed:</strong> ${j.files}</small></p>
                <p style="margin:0;"><small><strong>Details:</strong> ${j.message}</small></p>
              </div>
              <div style="margin-top:15px;padding-top:10px;border-top:1px solid rgba(0,0,0,0.1);">
                <small style="color:rgba(0,0,0,0.7);">✉️ <strong>Email report sent</strong> to your registered email address</small>
              </div>
            </div>
          `;
        }
        
        // Clear file input
        fileInput.value = '';
        
        // finalize overlay and hide after short delay
        if(overlay){
          overlay.querySelector('.processing-desc').textContent = `Done — ${j.result} (${j.score}%)`;
          const pb = overlay.querySelector('.progress-bar'); if(pb){ pb.style.width = `${j.score}%`; pb.textContent = `${j.score}%`; }
          setTimeout(()=>{ overlay.classList.remove('show'); }, 1800);
        }

        // Show email sent toast if backend confirms email was sent
        if(j.emailed){
          const toast = document.createElement('div');
          toast.style.position = 'fixed';
          toast.style.right = '20px';
          toast.style.top = '20px';
          toast.style.zIndex = 10000;
          toast.innerHTML = `<div class="alert alert-success shadow">✉️ Email sent successfully</div>`;
          document.body.appendChild(toast);
          setTimeout(()=>{ toast.classList.add('fade'); }, 50);
          setTimeout(()=>{ try{ toast.remove(); }catch(e){} }, 4000);
        }
      }catch(err){
        console.error('Error:', err);
        if(resultEl){
          resultEl.innerHTML = `
            <div class="alert alert-danger fade-in">
              <strong>❌ Upload Failed</strong>
              <br>Network error or server unavailable
              <br><small>${err.message}</small>
            </div>
          `;
        }
        // hide overlay
        const overlay = document.querySelector('.processing-overlay'); if(overlay){ overlay.classList.remove('show'); }
      }
    });
  });

  // admin block/unblock
  document.querySelectorAll('.block-btn').forEach(btn=>{
    btn.addEventListener('click', async ()=>{
      const id = btn.dataset.id;
      const action = btn.textContent.trim().toLowerCase().includes('block') ? 'block' : 'unblock';
      const fd = new FormData(); 
      fd.append('user_id', id); 
      fd.append('action', action);
      
      try{
        const res = await fetch('/admin/block',{method:'POST', body:fd});
        if(res.ok){ 
          location.reload(); 
        }
      }catch(err){
        console.error('Block action failed:', err);
      }
    });
  });
});


