### Run the program automatically 

* Create a new systemd service file for your from the file in this director `app.service`
```
cp -R ~/ai-access-gate/app.service /etc/systemd/system/
```
---
* Reload the systemd daemon to read the new service file
```
sudo systemctl daemon-reload
```
---
* Enable the service to start at boot time:
```
sudo systemctl enable app.service
```
This will create a symbolic link to app service file in the "/etc/systemd/system/multi-user.target.wants/" directory.

---
* Reboot to test if the program starts automatically at boot time:
```
sudo reboot
```
---

* After the reboot, app.service should start automatically. You can check the status of the service by running the following command:
```
sudo systemctl status app.service
```



