class Config:
    balance_file = "balance.txt"
    warehouse_file = "warehouse.txt"
    review_file = "review.txt"

    def create_files(self):
        for file_path in [self.balance_file, self.warehouse_file, self.review_file]:
            try:
                with open(file_path, "a"):
                    pass  # To create a new file if it does not exist.
            except Exception as e:
                print(f"Error creating {file_path}: {e}")