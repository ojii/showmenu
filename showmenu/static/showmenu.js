(function() {
  'use strict';

  angular.module('showmenu', ['ui.tree']).controller('MainCtrl', function($scope) {
    var socket = new WebSocket('ws://' + location.host);

    socket.onmessage = function(event){
      $scope.lock = true;
      $scope.menu = JSON.parse(event.data);
      $scope.$apply();
      $scope.lock = false;
    };

    socket.send_command = function(command, args){
      if (socket.readyState == 1 && !$scope.lock){
        socket.send(JSON.stringify([command, args]));
      }
    };

    socket.onopen = function(){
      socket.send_command('set_tree', [$scope.list]);
    };

    $scope.lock = false;
    $scope.from_level = 0;
    $scope.to_level = 100;
    $scope.extra_inactive = 100;
    $scope.extra_active = 100;
    $scope.list = [{
      "id": 1,
      "title": "1. dragon-breath",
      "items": []
    }, {
      "id": 2,
      "title": "2. moiré-vision",
      "items": [{
        "id": 21,
        "title": "2.1. tofu-animation",
        "items": [{
          "id": 211,
          "title": "2.1.1. spooky-giraffe",
          "items": []
        }
        ]
      }, {
        "id": 22,
        "title": "2.2. barehand-atomsplitting",
        "items": []
      },{
          "id": 212,
          "title": "2.1.2. bubble-burst",
          "items": []
        }]
    }, {
      "id": 3,
      "title": "3. unicorn-zapper",
      "items": []
    }, {
      "id": 4,
      "title": "4. romantic-transclusion",
      "items": []
    }];
    $scope.menu = [];
    $scope.selectedItem = {};
    $scope.options = {
      'dropped': function(event){
        socket.send_command('set_tree', [$scope.list]);
      }
    };
    $scope.menu_options = {};

    $scope.remove_node = function(scope) {
      scope.remove();
      socket.send_command('set_tree', [$scope.list])
    };

    $scope.toggle = function(scope) {
      scope.toggle();
    };

    $scope.newSubItem = function(scope) {
      var nodeData = scope.$modelValue;
      nodeData.items.push({
        id: nodeData.id * 10 + nodeData.items.length,
        title: nodeData.title + '.' + (nodeData.items.length + 1),
        items: []
      });
      socket.send_command('set_tree', [$scope.list]);
    };

    $scope.$watch('from_level', function(){
      socket.send_command('set_argument', ['from_level', $scope.from_level]);
    });
    $scope.$watch('to_level', function(){
      socket.send_command('set_argument', ['to_level', $scope.to_level]);
    });
    $scope.$watch('extra_inactive', function(){
      socket.send_command('set_argument', ['extra_inactive', $scope.extra_inactive]);
    });
    $scope.$watch('extra_active', function(){
      socket.send_command('set_argument', ['extra_active', $scope.extra_active]);
    });
  });
})();
