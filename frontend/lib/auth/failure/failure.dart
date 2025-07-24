class AppFailure {
  final String message;
  AppFailure([this.message = "Sorry an unexpected error has occured!"]);
  @override
  String toString() => 'AppFailure(message: $message)';
  
}
