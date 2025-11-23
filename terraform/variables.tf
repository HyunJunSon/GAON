variable "region" {
  description = "GCP Region"
  type        = string
  default     = "asia-northeast3"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
  default     = "asia-northeast3-a"
}

variable "machine_type" {
  description = "Backend VM machine type"
  type        = string
  default     = "e2-medium"
}

variable "disk_size" {
  description = "Boot disk size in GB"
  type        = number
  default     = 30
}

variable "db_user" {
  description = "PostgreSQL username"
  type        = string
  default     = "gaon_admin"
}

variable "db_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "gaon_db"
}
