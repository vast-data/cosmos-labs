import { writeFileSync } from 'fs';
import { config } from 'dotenv';

config();

const baseUrl = process.env['BASE_API_URL'] || 'http://localhost:8000';

// Create environment.ts (base file that Angular imports)
const envFileContent = `export const environment = {
  production: false,
  base_API_URL: '${baseUrl}'
};
`;

// Create environment.prod.ts (used in production builds via file replacement)
const envProdFileContent = `export const environment = {
  production: true,
  base_API_URL: '${baseUrl}'
};
`;

// Create both files - Angular uses environment.ts as the default import
// and replaces it with environment.prod.ts during production builds
writeFileSync('./src/environments/environment.ts', envFileContent);
writeFileSync('./src/environments/environment.prod.ts', envProdFileContent);
