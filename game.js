(() => {
  const canvas = document.getElementById('game');
  const ctx = canvas.getContext('2d');
  const scoreEl = document.getElementById('score');
  const bestEl = document.getElementById('best');
  const finalScoreEl = document.getElementById('finalScore');
  const finalBestEl = document.getElementById('finalBest');
  const titleEl = document.getElementById('title');
  const gameoverEl = document.getElementById('gameover');
  const startBtn = document.getElementById('startBtn');
  const retryBtn = document.getElementById('retryBtn');

  let W = 0, H = 0, DPR = 1;
  const state = {
    running: false,
    score: 0,
    best: parseInt(localStorage.getItem('ninjaDashBest') || '0', 10),
    time: 0,
    speed: 1,
    spawnTimer: 0,
    starTimer: 0,
    player: { x: 0, y: 0, r: 18, targetX: 0 },
    obstacles: [],
    stars: [],
    particles: [],
    stars_bg: [],
    pointerActive: false,
  };

  bestEl.textContent = state.best;

  function resize() {
    DPR = Math.min(window.devicePixelRatio || 1, 2);
    W = window.innerWidth;
    H = window.innerHeight;
    canvas.width = W * DPR;
    canvas.height = H * DPR;
    canvas.style.width = W + 'px';
    canvas.style.height = H + 'px';
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);

    if (state.player.x === 0) state.player.x = W / 2;
    state.player.targetX = state.player.x;
    state.player.y = H - 90;

    if (state.stars_bg.length === 0) {
      for (let i = 0; i < 60; i++) {
        state.stars_bg.push({
          x: Math.random() * W,
          y: Math.random() * H,
          r: Math.random() * 1.5 + 0.3,
          s: Math.random() * 0.3 + 0.1,
          tw: Math.random() * Math.PI * 2,
        });
      }
    }
  }

  function reset() {
    state.score = 0;
    state.time = 0;
    state.speed = 1;
    state.spawnTimer = 0;
    state.starTimer = 0;
    state.obstacles = [];
    state.stars = [];
    state.particles = [];
    state.player.x = W / 2;
    state.player.targetX = W / 2;
    scoreEl.textContent = '0';
  }

  function start() {
    reset();
    state.running = true;
    titleEl.classList.add('hidden');
    gameoverEl.classList.add('hidden');
    last = performance.now();
    requestAnimationFrame(loop);
  }

  function gameOver() {
    state.running = false;
    burst(state.player.x, state.player.y, '#ff6b6b', 30);
    if (state.score > state.best) {
      state.best = state.score;
      localStorage.setItem('ninjaDashBest', String(state.best));
      bestEl.textContent = state.best;
    }
    finalScoreEl.textContent = state.score;
    finalBestEl.textContent = state.best;
    setTimeout(() => gameoverEl.classList.remove('hidden'), 400);
  }

  function burst(x, y, color, count) {
    for (let i = 0; i < count; i++) {
      const a = Math.random() * Math.PI * 2;
      const sp = Math.random() * 4 + 1;
      state.particles.push({
        x, y,
        vx: Math.cos(a) * sp,
        vy: Math.sin(a) * sp,
        life: 1,
        color,
        size: Math.random() * 3 + 1.5,
      });
    }
  }

  function spawnObstacle() {
    const w = 36 + Math.random() * 30;
    state.obstacles.push({
      x: Math.random() * (W - w) + w / 2,
      y: -40,
      w,
      h: w,
      vy: 3 + Math.random() * 1.5,
      rot: Math.random() * Math.PI,
      vr: (Math.random() - 0.5) * 0.05,
    });
  }

  function spawnStar() {
    state.stars.push({
      x: Math.random() * (W - 40) + 20,
      y: -20,
      r: 12,
      vy: 2.5 + Math.random(),
      rot: 0,
      vr: 0.05,
    });
  }

  function update(dt) {
    state.time += dt;
    state.score += Math.floor(dt * 6);
    scoreEl.textContent = state.score;

    state.speed = 1 + Math.min(state.time / 25, 2.5);

    state.player.x += (state.player.targetX - state.player.x) * 0.22;

    state.spawnTimer -= dt;
    if (state.spawnTimer <= 0) {
      spawnObstacle();
      state.spawnTimer = Math.max(0.35, 0.9 - state.time * 0.012);
    }

    state.starTimer -= dt;
    if (state.starTimer <= 0) {
      spawnStar();
      state.starTimer = 1.4 + Math.random() * 1.2;
    }

    for (let i = state.obstacles.length - 1; i >= 0; i--) {
      const o = state.obstacles[i];
      o.y += o.vy * state.speed;
      o.rot += o.vr;
      if (o.y - o.h > H) {
        state.obstacles.splice(i, 1);
        continue;
      }
      const dx = o.x - state.player.x;
      const dy = o.y - state.player.y;
      const rr = state.player.r + o.w * 0.42;
      if (dx * dx + dy * dy < rr * rr) {
        gameOver();
        return;
      }
    }

    for (let i = state.stars.length - 1; i >= 0; i--) {
      const s = state.stars[i];
      s.y += s.vy * state.speed;
      s.rot += s.vr;
      if (s.y - s.r > H) {
        state.stars.splice(i, 1);
        continue;
      }
      const dx = s.x - state.player.x;
      const dy = s.y - state.player.y;
      const rr = state.player.r + s.r;
      if (dx * dx + dy * dy < rr * rr) {
        state.score += 10;
        scoreEl.textContent = state.score;
        burst(s.x, s.y, '#ffd93d', 12);
        state.stars.splice(i, 1);
      }
    }

    for (let i = state.particles.length - 1; i >= 0; i--) {
      const p = state.particles[i];
      p.x += p.vx;
      p.y += p.vy;
      p.vy += 0.15;
      p.life -= dt * 1.8;
      if (p.life <= 0) state.particles.splice(i, 1);
    }

    for (const bg of state.stars_bg) {
      bg.y += bg.s * state.speed;
      bg.tw += 0.05;
      if (bg.y > H) {
        bg.y = -2;
        bg.x = Math.random() * W;
      }
    }
  }

  function drawPlayer(x, y) {
    ctx.save();
    ctx.translate(x, y);

    ctx.shadowColor = 'rgba(78, 205, 196, 0.6)';
    ctx.shadowBlur = 18;

    ctx.fillStyle = '#2d3561';
    ctx.beginPath();
    ctx.arc(0, 0, 18, 0, Math.PI * 2);
    ctx.fill();

    ctx.shadowBlur = 0;
    ctx.fillStyle = '#4ecdc4';
    ctx.fillRect(-16, -4, 32, 5);

    ctx.fillStyle = '#fff';
    ctx.fillRect(-7, -2, 4, 2);
    ctx.fillRect(3, -2, 4, 2);

    ctx.fillStyle = '#ff6b6b';
    ctx.fillRect(-6, -1, 2, 1);
    ctx.fillRect(4, -1, 2, 1);

    ctx.restore();
  }

  function drawObstacle(o) {
    ctx.save();
    ctx.translate(o.x, o.y);
    ctx.rotate(o.rot);
    const g = ctx.createLinearGradient(0, -o.h / 2, 0, o.h / 2);
    g.addColorStop(0, '#ff8a8a');
    g.addColorStop(1, '#c93d3d');
    ctx.fillStyle = g;
    ctx.shadowColor = 'rgba(255, 107, 107, 0.5)';
    ctx.shadowBlur = 12;
    const r = 6;
    const w = o.w, h = o.h;
    ctx.beginPath();
    ctx.moveTo(-w / 2 + r, -h / 2);
    ctx.lineTo(w / 2 - r, -h / 2);
    ctx.quadraticCurveTo(w / 2, -h / 2, w / 2, -h / 2 + r);
    ctx.lineTo(w / 2, h / 2 - r);
    ctx.quadraticCurveTo(w / 2, h / 2, w / 2 - r, h / 2);
    ctx.lineTo(-w / 2 + r, h / 2);
    ctx.quadraticCurveTo(-w / 2, h / 2, -w / 2, h / 2 - r);
    ctx.lineTo(-w / 2, -h / 2 + r);
    ctx.quadraticCurveTo(-w / 2, -h / 2, -w / 2 + r, -h / 2);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  function drawStar(s) {
    ctx.save();
    ctx.translate(s.x, s.y);
    ctx.rotate(s.rot);
    ctx.fillStyle = '#ffd93d';
    ctx.shadowColor = '#ffd93d';
    ctx.shadowBlur = 18;
    ctx.beginPath();
    for (let i = 0; i < 5; i++) {
      const a = (i * Math.PI * 2) / 5 - Math.PI / 2;
      const x = Math.cos(a) * s.r;
      const y = Math.sin(a) * s.r;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
      const a2 = a + Math.PI / 5;
      ctx.lineTo(Math.cos(a2) * s.r * 0.45, Math.sin(a2) * s.r * 0.45);
    }
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  function render() {
    ctx.clearRect(0, 0, W, H);

    for (const bg of state.stars_bg) {
      const a = 0.4 + Math.sin(bg.tw) * 0.3;
      ctx.fillStyle = `rgba(255,255,255,${a})`;
      ctx.beginPath();
      ctx.arc(bg.x, bg.y, bg.r, 0, Math.PI * 2);
      ctx.fill();
    }

    for (const o of state.obstacles) drawObstacle(o);
    for (const s of state.stars) drawStar(s);

    if (state.running) drawPlayer(state.player.x, state.player.y);

    for (const p of state.particles) {
      ctx.fillStyle = p.color;
      ctx.globalAlpha = Math.max(0, p.life);
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
  }

  let last = 0;
  function loop(now) {
    const dt = Math.min((now - last) / 1000, 0.05);
    last = now;
    if (state.running) update(dt);
    render();
    if (state.running) requestAnimationFrame(loop);
    else render();
  }

  function handlePointer(clientX) {
    state.player.targetX = Math.max(state.player.r, Math.min(W - state.player.r, clientX));
  }

  canvas.addEventListener('touchstart', (e) => {
    e.preventDefault();
    if (!state.running) return;
    state.pointerActive = true;
    const t = e.touches[0];
    handlePointer(t.clientX);
  }, { passive: false });

  canvas.addEventListener('touchmove', (e) => {
    e.preventDefault();
    if (!state.running) return;
    const t = e.touches[0];
    handlePointer(t.clientX);
  }, { passive: false });

  canvas.addEventListener('touchend', (e) => {
    e.preventDefault();
    state.pointerActive = false;
  }, { passive: false });

  canvas.addEventListener('mousedown', (e) => {
    if (!state.running) return;
    state.pointerActive = true;
    handlePointer(e.clientX);
  });
  canvas.addEventListener('mousemove', (e) => {
    if (!state.running || !state.pointerActive) return;
    handlePointer(e.clientX);
  });
  window.addEventListener('mouseup', () => { state.pointerActive = false; });

  document.addEventListener('keydown', (e) => {
    if (!state.running) return;
    if (e.key === 'ArrowLeft') state.player.targetX = Math.max(state.player.r, state.player.targetX - 40);
    if (e.key === 'ArrowRight') state.player.targetX = Math.min(W - state.player.r, state.player.targetX + 40);
  });

  startBtn.addEventListener('click', start);
  retryBtn.addEventListener('click', start);

  window.addEventListener('resize', resize);
  window.addEventListener('orientationchange', resize);

  resize();
  render();
})();
