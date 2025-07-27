FROM node:18-alpine

WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy the rest of the application
COPY . .

# Fix TypeScript configuration for build
RUN sed -i 's/"allowImportingTsExtensions": true,/"allowImportingTsExtensions": true,\n    "noEmit": true,/' tsconfig.app.json

# Build the application
RUN npm run build

# Install serve to run the application
RUN npm install -g serve

EXPOSE 3000

# Use serve to run the application
CMD ["serve", "-s", "dist", "-l", "3000"]