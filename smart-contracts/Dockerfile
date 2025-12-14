FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy source
COPY . .

# Expose Hardhat node port
EXPOSE 8545

# Default command (overridden in compose for deployer)
CMD ["npx", "hardhat", "node", "--hostname", "0.0.0.0"]
