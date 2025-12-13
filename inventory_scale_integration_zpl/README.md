# ZPL Printer Integration for Weighbridge

## Overview
Professional ZPL thermal printer integration for the Weighbridge Scale Integration system. Supports Zebra and compatible thermal printers for automatic label and ticket printing.

## Features

### Printer Management
- **Multiple Connection Types**: Network (TCP/IP), USB/Serial
- **Printer Configuration**: DPI, label size, print speed, darkness
- **Connection Testing**: Real-time printer status monitoring
- **Multi-printer Support**: Assign different printers to scales and users
- **Cashier Integration**: ZPL print buttons in simplified cashier interface

### Auto-Print Capabilities
- **Auto-print Labels**: Automatically print labels when weighing is complete
- **Auto-print Tickets**: Print driver tickets after first weighing
- **Auto-print Certificates**: Generate certificates on completion
- **Manual Print**: On-demand printing from weighing records

### Print Job Management
- **Job Queue**: Track all print jobs with status
- **Retry Failed Jobs**: Automatic retry for failed prints
- **Print History**: Complete audit trail of all prints
- **Error Logging**: Detailed error messages for troubleshooting

### Smart Printer Assignment
1. **User Priority**: Uses user's default printer first
2. **Scale Assignment**: Falls back to scale's assigned printer
3. **System Default**: Uses first enabled printer as fallback

## Installation

### Prerequisites
```bash
# For USB printing (Linux)
sudo apt-get install python3-serial
```

**Note**: No external Python libraries required for network printing!

### Install Module
1. Copy module to `addons` directory
2. Update Apps List in Odoo
3. Install "Scale Integration - ZPL Printer"

## Configuration

### 1. Configure Printer
- Go to: Weighbridge → Configuration → ZPL Printers
- Click "Create"
- Set printer name and connection type
- Configure connection details:
  - **Network**: IP address and port (default 9100)
  - **USB**: Device path (e.g., /dev/usb/lp0 or COM1)
- Set label dimensions and print settings
- Click "Test Connection" to verify

### 2. Assign to Scale
- Open weighing scale configuration
- Go to "ZPL Printers" tab
- Add printers to use with this scale

### 3. Assign to Users
- Go to: Settings → Users & Companies → Users
- Edit user
- Go to "Weighing Scales" tab
- Set default ZPL printer
- Add assigned printers

### 4. Enable Auto-Print
- Open printer configuration
- Enable desired auto-print options:
  - Auto-print Label
  - Auto-print Ticket
  - Auto-print Certificate

## Usage

### Manual Printing
From any weighing record or cashier interface:
1. Click "🖨️ ZPL Label" - Print label (done state)
2. Click "🖨️ ZPL Ticket" - Print driver ticket (first state)
3. Click "🖨️ ZPL Certificate" - Print certificate (done state)

**Cashier Interface**: ZPL buttons automatically appear when cashier module is installed

### View Print Jobs
- Click "Print Jobs" button on weighing record
- Or go to: Weighbridge → Configuration → Print Jobs
- Retry failed jobs with "Retry" button

## ZPL Templates

### Label Format (A5 Landscape)
- Weighing reference number
- Truck plate and product
- Net weight (large)
- Gross and tare weights
- Date/time
- Barcode

### Ticket Format (80mm Thermal)
- Driver ticket header
- Weighing reference
- Truck plate
- Gross weight
- Barcode for scanning
- Instructions for driver

### Certificate Format (A4)
- Official certificate header
- Complete weighing details
- All weights with dates
- Partner and product info
- Scale information

## API Endpoints

### Print ZPL Code
```javascript
// POST /zpl/print
{
    "printer_id": 1,
    "zpl_code": "^XA^FO50,50^ADN,36,20^FDTest^FS^XZ",
    "job_name": "Custom Print"
}
```

### Get Printer Status
```javascript
// GET /zpl/printer/status/1
{
    "success": true,
    "status": "connected",
    "name": "Zebra ZT230",
    "is_enabled": true
}
```

## Troubleshooting

### Connection Issues
1. **Network Printer**:
   - Verify IP address and port
   - Check firewall settings
   - Ensure printer is on same network
   - Test with: `telnet <ip> <port>`

2. **USB Printer**:
   - Check device permissions: `ls -l /dev/usb/lp0`
   - Add user to lp group: `sudo usermod -a -G lp odoo`
   - Verify device path is correct



### Print Quality Issues
- Adjust darkness setting (0-30)
- Change print speed (slower = better quality)
- Verify DPI matches printer specification
- Check label size matches physical labels

### Auto-Print Not Working
- Verify auto-print is enabled in printer settings
- Check printer is assigned to scale or user
- Ensure printer status is "Connected"
- Review error logs in print jobs

## Supported Printers
- Zebra ZT Series (ZT230, ZT410, ZT420)
- Zebra ZD Series (ZD420, ZD620)
- Zebra GK/GX Series
- Any ZPL-compatible thermal printer

## Technical Details

### ZPL Command Structure
```zpl
^XA                    # Start format
^FO50,50              # Field origin (x,y)
^ADN,36,20            # Font (type, height, width)
^FDText^FS            # Field data
^BY3                  # Barcode width
^BCN,100,Y,N,N        # Barcode (type, height, print text)
^FDBarcode^FS         # Barcode data
^XZ                   # End format
```

### Print Job States
- **Pending**: Job created, waiting to print
- **Printing**: Currently sending to printer
- **Done**: Successfully printed
- **Failed**: Print error occurred

## Security
- Users need "Weighing Scale / User" group to print
- Only managers can configure printers
- Print jobs track user and timestamp
- Complete audit trail maintained

## Compatibility
- Odoo 19.0+
- Requires: inventory_scale_integration_base
- Optional: inventory_scale_integration_cashier (adds ZPL buttons to cashier)
- Optional: inventory_scale_integration_stock
- Works with all weighing modules
- Compatible with Odoo.sh and App Store (no external dependencies)

## Support
For issues or questions:
1. Check printer connection status
2. Review print job error messages
3. Verify printer configuration
4. Check Odoo server logs

## License
LGPL-3
