# Workshop Troubleshooting Guide

## 🎯 Quick Reference

This guide helps you resolve common issues during the VAST SDK workshop. Use this as a quick reference when things don't work as expected.

## 🚨 Common Issues & Solutions

### **Setup Issues**

#### **Problem: Python version is too old**
```
❌ Python 3.6.9 detected. Python 3.7+ required.
```

**Solutions:**
1. **Check current version:**
   ```bash
   python --version
   ```

2. **Upgrade Python:**
   - **macOS (Homebrew):** `brew upgrade python3`
   - **Ubuntu/Debian:** `sudo apt update && sudo apt install python3.7`
   - **Windows:** Download from https://python.org/downloads/

#### **Problem: Package installation fails with permission errors**
```
❌ Permission denied: '/usr/local/lib/python3.7/site-packages/vastpy'
```

**Solutions:**
1. **Use user installation:**
   ```bash
   pip install --user -r requirements.txt
   ```

2. **Use virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

#### **Problem: Package not found errors**
```
❌ ERROR: Could not find a version that satisfies the requirement vastpy
```

**Solutions:**
1. **Update pip:**
   ```bash
   pip install --upgrade pip
   ```

2. **Try again:**
   ```bash
   pip install -r requirements.txt
   ```

#### **Problem: Configuration file not found**
```
❌ FileNotFoundError: [Errno 2] No such file or directory: 'config.yaml'
```

**Solutions:**
1. **Check current directory:**
   ```bash
   pwd
   # Should be: /path/to/cosmos-labs
   ```

2. **Navigate to correct directory:**
   ```bash
   cd /path/to/cosmos-labs
   ```

3. **Copy example files:**
   ```bash
   cp config.yaml.example config.yaml
   cp secrets.yaml.example secrets.yaml
   ```

#### **Problem: YAML syntax errors**
```
❌ yaml.scanner.ScannerError: while scanning for the next token
```

**Solutions:**
1. **Validate YAML syntax:**
   ```bash
   python -c "import yaml; yaml.safe_load(open('config.yaml'))"
   python -c "import yaml; yaml.safe_load(open('secrets.yaml'))"
   ```

2. **Check indentation** - YAML is sensitive to spaces vs tabs
3. **Use a YAML validator** online if needed

### **Connection Issues**

#### **Problem: Cannot connect to VAST cluster**
```
❌ Connection failed: HTTPSConnectionPool(host='vast-cluster.com', port=443): Max retries exceeded
```

**Solutions:**
1. **Check network connectivity:**
   ```bash
   ping your-vast-cluster.com
   ```

2. **Verify HTTPS access:**
   ```bash
   curl -k https://your-vast-cluster.com/api/latest/clusters
   ```

3. **Check firewall settings** - Ensure port 443 is open

4. **Verify cluster address** - Make sure it's correct in `config.yaml`

#### **Problem: SSL certificate verification failed**
```
❌ Connection failed: SSL: CERTIFICATE_VERIFY_FAILED
```

**Solutions:**
1. **For testing only** - Set `ssl_verify: false` in `config.yaml`:
   ```yaml
   vast:
     ssl_verify: false
   ```

2. **For production** - Install proper SSL certificates

3. **Check certificate validity:**
   ```bash
   openssl s_client -connect your-vast-cluster.com:443
   ```

#### **Problem: Authentication failed**
```
❌ Connection failed: 401 Unauthorized
```

**Solutions:**
1. **Check credentials** in `secrets.yaml`:
   ```yaml
   vast_password: "your-correct-password"
   ```

2. **Verify username** in `config.yaml`:
   ```yaml
   vast:
     user: "your-correct-username"
   ```

3. **Check user permissions** - Ensure user has read access

### **Configuration Issues**

#### **Problem: Configuration file not found**
```
❌ Error: [Errno 2] No such file or directory: 'config.yaml'
```

**Solutions:**
1. **Check current directory:**
   ```bash
   pwd
   # Should be: /path/to/cosmos-labs
   ```

2. **Navigate to correct directory:**
   ```bash
   cd /path/to/cosmos-labs
   ```

3. **Copy example files:**
   ```bash
   cp config.yaml.example config.yaml
   cp secrets.yaml.example secrets.yaml
   ```

#### **Problem: YAML syntax error**
```
❌ Error: while parsing a block mapping
```

**Solutions:**
1. **Check YAML indentation** - Use spaces, not tabs
2. **Validate YAML syntax:**
   ```bash
   python -c "import yaml; yaml.safe_load(open('config.yaml'))"
   ```

3. **Check for missing colons** after keys
4. **Ensure proper nesting** of configuration sections

#### **Problem: Missing configuration values**
```
❌ Error: Key 'vast.address' not found in configuration
```

**Solutions:**
1. **Check `config.yaml` structure:**
   ```yaml
   vast:
     address: "https://your-vast-cluster.com"
     user: "your-username"
   ```

2. **Verify all required keys** are present
3. **Check for typos** in configuration keys

### **Python Environment Issues**

#### **Problem: Module not found**
```
❌ ImportError: No module named 'vastpy'
```

**Solutions:**
1. **Install missing packages:**
   ```bash
   pip install vastpy vastdb pyyaml
   ```

2. **Install from requirements.txt:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Check Python path:**
   ```bash
   python -c "import sys; print(sys.path)"
   ```

4. **Use virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

#### **Problem: Python version too old**
```
❌ Error: Python 3.7+ required
```

**Solutions:**
1. **Check Python version:**
   ```bash
   python --version
   ```

2. **Upgrade Python:**
   - **Windows:** Download from https://python.org/downloads/
   - **macOS:** `brew upgrade python3`
   - **Linux:** `sudo apt install python3.7`

3. **Use python3 command:**
   ```bash
   python3 --version
   python3 01_connect_to_vast.py
   ```

### **VAST Database Issues**

#### **Problem: Database connection failed**
```
❌ Error: is not a VAST DB server endpoint
```

**Solutions:**
1. **Check endpoint** in `config.yaml`:
   ```yaml
   vastdb:
     endpoint: "https://your-vast-db-cluster.com"  # Not VMS endpoint
   ```

2. **Verify S3 credentials** in `secrets.yaml`:
   ```yaml
   s3_access_key: "your-s3-access-key"
   s3_secret_key: "your-s3-secret-key"
   ```

3. **Contact VAST administrator** for correct database endpoint

#### **Problem: S3 credentials invalid**
```
❌ Error: InvalidAccessKeyId
```

**Solutions:**
1. **Check S3 credentials** in `secrets.yaml`
2. **Verify credentials** are correct and active
3. **Check S3 permissions** for database access
4. **Use same credentials** as S3 access

### **Permission Issues**

#### **Problem: Permission denied**
```
❌ Error: Permission denied: 'config.yaml'
```

**Solutions:**
1. **Check file permissions:**
   ```bash
   ls -la config.yaml
   ```

2. **Fix permissions:**
   ```bash
   chmod 644 config.yaml
   chmod 600 secrets.yaml
   ```

3. **Check directory permissions:**
   ```bash
   ls -la .
   ```

#### **Problem: Cannot write to directory**
```
❌ Error: Permission denied: '/path/to/cosmos-labs'
```

**Solutions:**
1. **Check directory ownership:**
   ```bash
   ls -la .
   ```

2. **Change ownership:**
   ```bash
   sudo chown -R $USER:$USER /path/to/cosmos-labs
   ```

3. **Use user directory:**
   ```bash
   cd ~/cosmos-labs
   ```

### **Network Issues**

#### **Problem: Timeout errors**
```
❌ Error: ReadTimeoutError
```

**Solutions:**
1. **Increase timeout** in `config.yaml`:
   ```yaml
   vast:
     timeout: 60  # Increase from 30
   ```

2. **Check network stability:**
   ```bash
   ping -c 10 your-vast-cluster.com
   ```

3. **Try different network** if possible

#### **Problem: DNS resolution failed**
```
❌ Error: Name or service not known
```

**Solutions:**
1. **Check DNS settings:**
   ```bash
   nslookup your-vast-cluster.com
   ```

2. **Try IP address** instead of hostname
3. **Check `/etc/hosts`** file for local overrides
4. **Use different DNS server** (8.8.8.8, 1.1.1.1)

## 🔍 Debugging Steps

### **Step 1: Verify Basic Setup**
```bash
# Check Python version
python --version

# Check current directory
pwd

# Check repository structure
ls -la

# Check configuration files
ls -la config.yaml secrets.yaml
```

### **Step 2: Test Dependencies**
```bash
# Test Python imports
python -c "import vastpy; print('vastpy OK')"
python -c "import vastdb; print('vastdb OK')"
python -c "import yaml; print('yaml OK')"
```

### **Step 3: Test Configuration**
```bash
# Test configuration loading
python -c "from config_loader import ConfigLoader; c=ConfigLoader('config.yaml', 'secrets.yaml'); print('Config OK')"
```

### **Step 4: Test Network Connectivity**
```bash
# Test basic connectivity
ping your-vast-cluster.com

# Test HTTPS access
curl -k https://your-vast-cluster.com/api/latest/clusters
```

### **Step 5: Test VAST Connection**
```bash
# Test VAST connection
cd examples
python 01_connect_to_vast.py
```

## 🛠️ Advanced Troubleshooting

### **Enable Debug Logging**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Your code here
```

### **Check VAST API Directly**
```bash
# Test VAST API with curl
curl -k -u "username:password" https://your-vast-cluster.com/api/latest/clusters
```

### **Verify SSL Certificates**
```bash
# Check certificate details
openssl s_client -connect your-vast-cluster.com:443 -servername your-vast-cluster.com
```

### **Test S3 Credentials**
```python
import boto3

# Test S3 credentials
s3 = boto3.client(
    's3',
    endpoint_url='https://your-vast-cluster.com',
    aws_access_key_id='your-access-key',
    aws_secret_access_key='your-secret-key',
    verify=False
)

# List buckets
response = s3.list_buckets()
print(response)
```

## 🎓 Workshop-Specific Issues

### **Problem: Participant can't follow along with examples**
```
❌ "I'm getting different output than what's shown"
```

**Solutions:**
1. **Check VAST cluster differences:**
   - Different cluster configurations may show different data
   - This is normal and expected
   - Focus on understanding the concepts, not exact output

2. **Verify configuration:**
   - Ensure `config.yaml` and `secrets.yaml` are correct
   - Check if using different VAST cluster than instructor

3. **Ask for help:**
   - Raise hand during Q&A periods
   - Ask instructor to review your configuration

### **Problem: Examples run too slowly for workshop pace**
```
❌ "The script is taking too long to complete"
```

**Solutions:**
1. **Skip to next example:**
   - Use Ctrl+C to stop current example
   - Move to next example with group
   - Return to slow example later

2. **Use smaller datasets:**
   - Some examples can be modified for faster execution
   - Ask instructor for quick alternatives

### **Problem: Different experience levels causing confusion**
```
❌ "Some people are way ahead/behind"
```

**Solutions:**
1. **For advanced participants:**
   - Help neighbors who are struggling
   - Explore additional features in examples
   - Ask instructor for advanced challenges

2. **For beginners:**
   - Don't worry about keeping up perfectly
   - Focus on understanding concepts
   - Ask questions freely

## 📞 Getting Help

### **During the Workshop**
1. **Ask questions** during designated Q&A periods
2. **Use this troubleshooting guide** for quick fixes
3. **Ask your neighbor** for help
4. **Check the example scripts** for reference

### **After the Workshop**
1. **Review the documentation** in each lab directory
2. **Try running the examples** in your own environment
3. **Build your own solutions** using these as templates
4. **Join the VAST community** for ongoing support

### **Keep in touch!**
- **VAST support:** https://support.vastdata.com/s/
- **Community forum:** https://community.vastdata.com

## 🎯 Success Indicators

Your setup is working correctly when:

- [ ] **All examples run** without errors
- [ ] **VAST connection test** shows cluster information
- [ ] **Configuration files** are properly set up
- [ ] **Dependencies** are installed and working
- [ ] **Network connectivity** is stable
- [ ] **Credentials** are correct and active

## 📚 Additional Resources

- **VAST Documentation:** https://support.vastdata.com/s/
- **vastpy GitHub:** https://github.com/vast-data/vastpy
- **vastdb GitHub:** https://github.com/vast-data/vastdb_sdk
- **Python Documentation:** https://docs.python.org/3/
- **YAML Documentation:** https://yaml.org/

---

*"Troubleshooting is part of the learning process. Every problem you solve makes you a better developer."*
