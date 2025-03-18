package main

import "github.com/shirou/gopsutil/v4/disk"
import "fmt"

func main() {
	// only get physical drives
	parts, _ := disk.Partitions(false)

	fmt.Println("disk.Partitions(false) called", "number of parts", len(parts))


	for _, disk := range parts {
		fmt.Println("Returned disk by disk.Partition()", "device", disk.Device,
			"mountpoint", disk.Mountpoint, "fstype", disk.Fstype)
	}

	parts, _ = disk.Partitions(true)

	fmt.Println("disk.Partitions(true) called", "number of parts", len(parts))


	for _, disk := range parts {
		fmt.Println("Returned disk by disk.Partition()", "device", disk.Device,
			"mountpoint", disk.Mountpoint, "fstype", disk.Fstype)
	}
}