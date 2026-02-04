#!/usr/bin/env node
/**
 * CI/CD Validation Script for catalog-index.json
 * 
 * Validates:
 * 1. JSON syntax
 * 2. Required fields present
 * 3. No duplicate component IDs within domains
 * 4. Component count matches actual components array length
 * 5. All referenced files exist
 * 
 * Exit codes:
 * 0 - All validations passed
 * 1 - Validation errors found
 */

const fs = require('fs');
const path = require('path');

const CATALOG_PATH = path.join(__dirname, '..', 'catalog-index.json');
const LIBRARY_ROOT = path.join(__dirname, '..');

let errors = [];
let warnings = [];

function error(msg) {
  errors.push(`ERROR: ${msg}`);
  console.error(`\x1b[31mERROR:\x1b[0m ${msg}`);
}

function warn(msg) {
  warnings.push(`WARNING: ${msg}`);
  console.warn(`\x1b[33mWARNING:\x1b[0m ${msg}`);
}

function info(msg) {
  console.log(`\x1b[36mINFO:\x1b[0m ${msg}`);
}

function success(msg) {
  console.log(`\x1b[32mPASS:\x1b[0m ${msg}`);
}

// 1. Check JSON syntax
info('Validating JSON syntax...');
let catalog;
try {
  const content = fs.readFileSync(CATALOG_PATH, 'utf-8');
  catalog = JSON.parse(content);
  success('JSON syntax valid');
} catch (e) {
  error(`Invalid JSON: ${e.message}`);
  process.exit(1);
}

// 2. Check required fields
info('Validating required fields...');
const requiredFields = ['schema_version', 'last_updated', 'total_components', 'domains'];
for (const field of requiredFields) {
  if (!(field in catalog)) {
    error(`Missing required field: ${field}`);
  }
}
if (!errors.length) {
  success('All required fields present');
}

// 3. Validate domains
info('Validating domain structure...');
const globalIds = new Set();

for (const [domainName, domainData] of Object.entries(catalog.domains || {})) {
  // Check domain has required fields
  if (!('count' in domainData)) {
    error(`Domain "${domainName}" missing "count" field`);
  }
  if (!('components' in domainData)) {
    error(`Domain "${domainName}" missing "components" array`);
    continue;
  }
  
  // Check count matches array length
  const actualCount = domainData.components.length;
  if (domainData.count !== actualCount) {
    error(`Domain "${domainName}": count (${domainData.count}) doesn't match components array length (${actualCount})`);
  }
  
  // Check for duplicate IDs within domain
  const domainIds = new Set();
  for (const comp of domainData.components) {
    if (!comp.id) {
      error(`Domain "${domainName}": component missing "id" field`);
      continue;
    }
    
    if (domainIds.has(comp.id)) {
      error(`Domain "${domainName}": duplicate component ID "${comp.id}"`);
    }
    domainIds.add(comp.id);
    
    // Track global duplicates (warn only)
    if (globalIds.has(comp.id)) {
      warn(`Component ID "${comp.id}" appears in multiple domains`);
    }
    globalIds.add(comp.id);
    
    // Check component location exists
    if (comp.location) {
      const compPath = path.join(LIBRARY_ROOT, comp.location);
      if (!fs.existsSync(compPath)) {
        warn(`Component "${comp.id}" location doesn't exist: ${comp.location}`);
      }
    }
  }
}

// 4. Validate total count
info('Validating total component count...');
let actualTotal = 0;
for (const domainData of Object.values(catalog.domains || {})) {
  actualTotal += (domainData.components || []).length;
}
if (catalog.total_components !== actualTotal) {
  error(`total_components (${catalog.total_components}) doesn't match sum of domain components (${actualTotal})`);
} else {
  success(`Total component count matches: ${actualTotal}`);
}

// Summary
console.log('\n--- Validation Summary ---');
console.log(`Domains: ${Object.keys(catalog.domains || {}).length}`);
console.log(`Components: ${actualTotal}`);
console.log(`Errors: ${errors.length}`);
console.log(`Warnings: ${warnings.length}`);

if (errors.length > 0) {
  console.log('\n\x1b[31mValidation FAILED\x1b[0m');
  process.exit(1);
} else {
  console.log('\n\x1b[32mValidation PASSED\x1b[0m');
  process.exit(0);
}
