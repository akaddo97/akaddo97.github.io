/* Nav movement, both halves of it.

   ARRIVAL. The labels start stacked on one point and spring out to their own
   positions, nearest first, so the row unpacks. That point is the nav item for
   the page you are on: land on /learn/ and the row unpacks out of [AI fluency].
   Home has no current item, so it falls back to the centre square, which is
   home, and the effect there is unchanged.

   EXIT. Click a nav link and the other labels fold into the one you clicked
   before the page changes, so the arrival on the next page continues the same
   movement rather than starting a new one.

   Driven by the Web Animations API rather than by inline styles and a cleanup
   timer. That matters: the inline-style version could be left stranded at
   opacity zero if the browser throttled the tab part way through, which is what
   a background tab does. A Web Animation holds its start state only for its own
   delay and then hands the element back to the stylesheet.

   The exit does fill forwards, which the back button would otherwise restore
   from the bfcache mid-fold, so pageshow cancels everything and re-enters.

   The start state is set by script on purpose. With JavaScript off the nav just
   renders, rather than being stuck invisible. */
(function(){
  var row=document.querySelector('.navrow');
  if(row===null){return;}
  var reduce=window.matchMedia('(prefers-reduced-motion:reduce)');
  var wide=window.matchMedia('(min-width:721px)');
  function off(){
    if(typeof Element.prototype.animate==='undefined'){return true;}
    if(reduce.matches){return true;}
    return wide.matches===false;
  }

  var DUR=520, STAGGER=55, SCALE=0.45, MARKMS=120, EXIT=260, EXITSTEP=40;
  var EASE='cubic-bezier(0.34,1.55,0.64,1)';
  var OUTEASE='cubic-bezier(0.4,0,1,1)';
  var markHome=row.querySelector('.mark-home');

  function visible(el){return el!==null&&el.offsetParent!==null;}
  function centre(el){var b=el.getBoundingClientRect();return b.left+b.width/2;}
  function labels(){
    return Array.prototype.slice.call(row.querySelectorAll('a'))
      .filter(function(el){return el!==markHome&&visible(el);});
  }
  function everything(){
    var all=labels();
    if(visible(markHome)){all.push(markHome);}
    return all;
  }

  function origin(){
    var cur=row.querySelector('a[aria-current="page"]');
    if(visible(cur)){return cur;}
    return markHome;
  }

  function enter(){
    if(off()||document.visibilityState==='hidden'){return;}
    var o=origin();
    if(visible(o)===false){return;}
    var ox=centre(o);
    if(visible(markHome)){
      markHome.animate([{transform:'scale(0.55)'},{transform:'none'}],
        {duration:340,easing:'cubic-bezier(0.34,1.5,0.64,1)',fill:'backwards'});
      markHome.animate([{opacity:0},{opacity:1}],
        {duration:220,easing:'linear',fill:'backwards'});
    }
    var plan=labels().map(function(el){return {el:el,dx:ox-centre(el)};});
    plan.slice().sort(function(a,b){return Math.abs(a.dx)-Math.abs(b.dx);})
      .forEach(function(p,i){p.delay=MARKMS+i*STAGGER;});
    plan.forEach(function(p){
      p.el.animate(
        [{transform:'translateX('+p.dx.toFixed(1)+'px) scale('+SCALE+')'},
         {transform:'none'}],
        {duration:DUR,delay:p.delay,easing:EASE,fill:'backwards'});
      p.el.animate([{opacity:0},{opacity:1}],
        {duration:240,delay:p.delay,easing:'linear',fill:'backwards'});
    });
    row.setAttribute('data-nav-in','done');
  }

  function fold(target,done){
    var ox=centre(target);
    var plan=everything().filter(function(el){return el!==target;})
      .map(function(el){return {el:el,dx:ox-centre(el)};});
    plan.slice().sort(function(a,b){return Math.abs(b.dx)-Math.abs(a.dx);})
      .forEach(function(p,i){p.delay=i*EXITSTEP;});
    plan.forEach(function(p){
      p.el.animate(
        [{transform:'none',opacity:1},
         {transform:'translateX('+p.dx.toFixed(1)+'px) scale('+SCALE+')',opacity:0}],
        {duration:EXIT,delay:p.delay,easing:OUTEASE,fill:'forwards'});
    });
    window.setTimeout(done,EXIT+60);
  }

  /* Hold the page change only for a click we are certain we are the ones
     about to satisfy. A new tab, a modified click, a download, an outbound
     link or a link to this same page all navigate the ordinary way. */
  function ours(e,a){
    if(e.defaultPrevented){return false;}
    if(e.button!==0){return false;}
    if(e.metaKey||e.ctrlKey||e.shiftKey||e.altKey){return false;}
    if(a.target!==''&&a.target!=='_self'){return false;}
    if(a.hasAttribute('download')){return false;}
    if(a.origin!==window.location.origin){return false;}
    if(a.getAttribute('aria-current')==='page'){return false;}
    return true;
  }

  var leaving=false;
  row.addEventListener('click',function(e){
    if(typeof e.target.closest==='undefined'){return;}
    var a=e.target.closest('a');
    if(a===null||row.contains(a)===false){return;}
    if(off()||leaving||ours(e,a)===false){return;}
    e.preventDefault();
    leaving=true;
    var href=a.href;
    function go(){window.location.href=href;}
    try{fold(a,go);}catch(err){go();}
  });

  window.addEventListener('pageshow',function(e){
    if(e.persisted!==true){return;}
    leaving=false;
    everything().forEach(function(el){
      if(typeof el.getAnimations==='undefined'){return;}
      el.getAnimations().forEach(function(an){an.cancel();});
    });
    enter();
  });

  var fired=false;
  function once(){if(fired){return;}fired=true;enter();}
  if(document.fonts&&document.fonts.ready){document.fonts.ready.then(once,once);}
  window.setTimeout(once,400);
})();
