// Interaction only: the theme switch and the blast-radius graph. This file holds no digit at all
// (see the site README): sizes and colours come from CSS custom properties, the graph's data from the
// embedded JSON element, and every number on the page is in the static HTML.
(function () {
  'use strict';
  var root = document.documentElement;
  var cy = null;

  function stored() {
    try { return localStorage.getItem('akg-theme'); } catch (e) { return null; }
  }
  function remember(theme) {
    try { localStorage.setItem('akg-theme', theme); } catch (e) { /* private mode: not kept */ }
  }
  function isDark() {
    var set = root.getAttribute('data-theme');
    if (set) { return set === 'dark'; }
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
  if (stored()) { root.setAttribute('data-theme', stored()); }
  document.getElementById('theme-toggle').addEventListener('click', function () {
    var next = isDark() ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    remember(next);
    if (cy) { cy.style(graphStyle()); }
  });

  function token(name) { return getComputedStyle(root).getPropertyValue(name).trim(); }

  function graphStyle() {
    return [
      { selector: 'node', style: {
        'label': 'data(label)', 'font-size': token('--graph-font'), 'color': token('--text'),
        'background-color': token('--node'), 'width': token('--node-size'), 'height': token('--node-size'),
        'text-wrap': 'ellipsis', 'text-max-width': token('--label-width'), 'text-valign': 'bottom',
        'text-margin-y': token('--label-gap') } },
      { selector: 'node[kind = "system"]', style: {
        'background-color': token('--accent'), 'width': token('--system-size'), 'height': token('--system-size') } },
      { selector: 'node[kind = "unit"]', style: { 'background-color': token('--unit'), 'shape': 'round-rectangle' } },
      { selector: 'node[kind = "control"]', style: { 'background-color': token('--control') } },
      { selector: 'node[kind = "risk"]', style: { 'background-color': token('--risk'), 'shape': 'diamond' } },
      { selector: 'node[kind = "entity"]', style: { 'background-color': token('--entity'), 'shape': 'hexagon' } },
      { selector: 'edge', style: { 'width': token('--edge-width'), 'line-color': token('--edge'), 'curve-style': 'straight' } }
    ];
  }

  var container = document.getElementById('graph');
  var source = document.getElementById('site-data');
  if (!container || !source) { return; }
  if (typeof cytoscape === 'undefined') {
    container.classList.add('unavailable');
    return;
  }

  var data = JSON.parse(source.textContent);
  var byId = {};
  data.nodes.forEach(function (n) { byId[n.id] = n; });
  var system = data.nodes.filter(function (n) { return n.kind === 'system'; }).shift();
  var units = data.nodes.filter(function (n) { return n.kind === 'unit'; });
  var open = {};
  var ring = ['entity', 'risk', 'control', 'unit', 'system'];

  function edgesOf(kind, test) {
    return data.edges.filter(function (e) { return e.kind === kind && test(e); });
  }

  function elements() {
    var nodes = {};
    var edges = {};
    nodes[system.id] = true;
    units.forEach(function (u) {
      nodes[u.id] = true;
      if (!open[u.id]) { edges['via:' + u.id] = { id: 'via:' + u.id, source: system.id, target: u.id }; }
    });
    Object.keys(open).forEach(function (unitId) {
      var entities = {};
      edgesOf('owned_by', function (e) { return e.target === unitId; }).forEach(function (e) { entities[e.source] = e; });
      var risks = {};
      edgesOf('exposes', function (e) { return entities[e.target]; }).forEach(function (e) { risks[e.source] = true; addEdge(e); });
      var controls = {};
      edgesOf('mitigates', function (e) { return risks[e.target]; }).forEach(function (e) { controls[e.source] = true; addEdge(e); });
      edgesOf('depends_on', function (e) { return controls[e.target]; }).forEach(addEdge);
      Object.keys(entities).forEach(function (id) { addEdge(entities[id]); });
      [entities, risks, controls].forEach(function (set) { Object.keys(set).forEach(function (id) { nodes[id] = true; }); });
    });
    function addEdge(e) { edges[e.source + '>' + e.target] = { id: e.source + '>' + e.target, source: e.source, target: e.target }; }
    return Object.keys(nodes).map(function (id) {
      return { group: 'nodes', data: { id: id, label: byId[id].label, kind: byId[id].kind } };
    }).concat(Object.keys(edges).map(function (id) { return { group: 'edges', data: edges[id] }; }));
  }

  function draw() {
    cy.elements().remove();
    cy.add(elements());
    cy.layout({
      name: 'concentric',
      concentric: function (n) { return ring.indexOf(n.data('kind')); },
      levelWidth: function () { return Number.MIN_VALUE; },
      spacingFactor: parseFloat(token('--ring-spacing')),
      minNodeSpacing: parseFloat(token('--node-gap')),
      avoidOverlap: true,
      fit: true
    }).run();
  }

  cy = cytoscape({ container: container, style: graphStyle() });
  cy.on('tap', 'node[kind = "unit"]', function (event) {
    var id = event.target.id();
    if (open[id]) { delete open[id]; } else { open[id] = true; }
    draw();
  });
  draw();
}());
