void main() {
  var key = 'test';
  var pattern = '{{\${key}}}';
  print('Pattern: $pattern');
  print('Expected: {{test}}');
  print('Match: ${pattern == '{{test}}'}');
}
