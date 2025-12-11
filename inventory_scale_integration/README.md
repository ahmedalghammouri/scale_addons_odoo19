# Inventory Scale Integration - Multi-Scale Support

## Overview
This module now supports multiple weighing scales with centralized configuration, user assignment, and connection monitoring.

## Features

### 1. Weighing Scale Configuration (`weighing.scale`)
- **IP Address & Port**: Configure connection details for each scale
- **Enable/Disable**: Control which scales are active
- **Connection Monitoring**: Real-time status tracking (Connected/Disconnected/Error)
- **Last Read Values**: Track last weight reading with timestamp
- **User Assignment**: Assign specific users to each scale
- **Test Connection**: Button to verify scale connectivity

### 2. User Scale Assignment
- **Default Scale**: Each user can have a default scale assigned
- **Assigned Scales**: Users can be assigned to multiple scales
- **Automatic Selection**: Default scale is auto-selected when creating weighing records

### 3. Truck Weighing Integration
- **Scale Selection**: Choose from assigned scales in weighing records
- **Dynamic Domain**: Only enabled scales assigned to the user are available
- **Override Option**: Users can change the scale if needed
- **Connection Tracking**: All weight readings are tracked with scale information

## Configuration

### Step 1: Configure Scales
1. Go to **Weighbridge Management > Scale Configuration**
2. Create a new scale record
3. Set:
   - Name (e.g., "Scale 1 - Warehouse A")
   - IP Address (e.g., "192.168.1.100")
   - Port (default: 5000)
   - Timeout (default: 2 seconds)
4. Click **Test Connection** to verify
5. Enable the scale

### Step 2: Assign Users to Scales
1. Go to **Settings > Users & Companies > Users**
2. Select a user
3. Go to **Weighing Scales** tab
4. Set:
   - **Default Weighing Scale**: Primary scale for this user
   - **Assigned Scales**: All scales this user can access

### Step 3: Use in Weighing Records
1. Create a new **Truck Weighing** record
2. The **Weighing Scale** field will auto-populate with user's default scale
3. Change scale if needed (only assigned scales are available)
4. Click **Fetch Live Weight** to read from the selected scale

## Security Groups
- **Weighing Scale / User**: Can use scales and create weighing records
- **Weighing Scale / Manager**: Can configure scales and manage all settings

## Technical Details

### Models
- `weighing.scale`: Scale configuration and monitoring
- `res.users`: Extended with scale assignment fields
- `truck.weighing`: Updated to use configured scales

### Key Methods
- `weighing.scale.get_weight()`: Read weight from scale
- `weighing.scale.action_test_connection()`: Test scale connectivity
- `truck.weighing.action_fetch_live_weight()`: Fetch weight using selected scale

### Connection Monitoring
- Status updated on each read attempt
- Last read weight and timestamp tracked
- Error messages stored for troubleshooting
